"""Authentication for Google.

This was based on
[aiohttp-login](https://github.com/imbolc/aiohttp-login/), which at
the time worked with outdated Google APIs and require Jinja2. Oren
modernized this. Piotr integrated this into the system.

Portions of this file, from aiohttp-login, are licensed as:

Copyright (c) 2011 Imbolc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

Eventually, this should be broken out into its own module.
"""

import base64
import functools
import json
import sys
import yaml
import yarl

import aiohttp
import aiohttp.web
import aiohttp_session

# TODO: We might want to not import this, but pass this info, to make
# this file generic, and not specific to learning_observer.
import learning_observer.settings as settings


# TODO: Importing these here breaks abstractions.
#
# We want the auth code to be generic and reusable (eventually its own
# module)
import learning_observer.paths as paths
import learning_observer.exceptions

if isinstance(settings.settings['auth']['google-oauth']['web']['client_secret'], dict) or \
   isinstance(settings.settings['auth']['google-oauth']['web']['project_id'], dict) or \
   isinstance(settings.settings['auth']['google-oauth']['web']['client_id'], dict):
    print("Please configure Google oauth")
    print("")
    print("Go to:")
    print("  https://console.developers.google.com/")
    print("And set up an OAuth client for a web application. Make sure that configuration")
    print("mirrors the one here.")
    sys.exit(-1)


async def verify_teacher_account(user_id, email):
    '''
    Confirm the teacher is registered with the system. Eventually, we will want
    3 versions of this:
    * Always true (open system)
    * Text file backed (pilots, small deploys)
    * Database-backed (large-scale deploys)

    For now, we have the file-backed version
    '''
    teachers = yaml.safe_load(open(paths.data("teachers.yaml")))
    if email not in teachers:
        print("Email not found in teachers")
        return False
    if teachers[email]["google_id"] != user_id:
        print("Non-matching Google ID")
        return False
    print("Teacher account verified")
    return True


async def _authorize_user(request, user):
    """
    Log a user into our session. This will update the (encrypted) user
    session with the user's identity, and whether they are authorized.

    :param request: web request.
    :param user_id: provider's user ID (e.g., Google ID).

    """
    session = await aiohttp_session.get_session(request)
    session["user"] = user
    if user.get("authorized", False):
        return True
    return await verify_teacher_account(user['user_id'], user['email'])


async def logout(request):
    """
    Handles sign out. This is generic - does not depend on which
    social ID is logged in (Google/Facebook/...).
    """
    session = await aiohttp_session.get_session(request)
    session.pop("user", None)
    session.pop("auth_headers", None)
    return aiohttp.web.HTTPFound("/")  # TODO: Make a proper logout page


@aiohttp.web.middleware
async def auth_middleware(request, handler):
    '''
    Move user into the request

    Save user into a cookie
    '''
    session = await aiohttp_session.get_session(request)
    request['user'] = session.get('user', None)
    request['auth_headers'] = session.get('auth_headers', None)
    resp = await handler(request)
    if request['user'] is None:
        userinfo = None
    else:
        userinfo = {
            "name": request['user']['name'],
            "picture": request['user']['picture'],
            "authorized": request['user']['authorized'],
            "google_id": request['user']['user_id'],
            "email": request['user']['email']
        }
    # This is a dumb way to sanitize data and pass it to the front-end.
    #
    # Cookies tend to get encoded and decoded in ad-hoc strings a lot, often
    # in non-compliant ways (to see why, try to find the spec for cookies!)
    #
    # This avoids bugs (and, should the issue come up, security issues
    # like injections)
    #
    # This should really be abstracted away into a library which passes state
    # back-and-forth, but for now, this works.
    resp.set_cookie(
        "userinfo",
        base64.b64encode(json.dumps(userinfo).encode('utf-8')).decode('utf-8')
    )
    return resp


async def user_info(request):
    '''
    This is a handler which currently shows:
    * Google user ID
    * E-mail
    * First and family name
    * Google avatar
    * And whether the user is authorized

    This is helpful for things like the little avatar when rendering the
    page.

    TODO: Think through what info we want to give as we add authentication
    methods. We don't want to leak data accidentally.
    '''
    return aiohttp.web.json_response(request['user'])


def html_login_required(handler):
    """
    A handler function decorator that enforces that the user is logged
    in. If not, redirects to the login page.

    :param handler: function to decorate.
    :return: decorated function
    """
    @functools.wraps(handler)
    async def decorator(*args):
        user = args[0]["user"]
        if user is None:
            return aiohttp.web.HTTPFound("/")
        return handler(*args)
    return decorator


#
# Below is Google-specific code. This should go in its own file?
#

async def social(request):
    """Handles Google sign in.

    Provider is in `request.match_info['provider']` (currently, only Google)
    """
    if request.match_info['provider'] != 'google':
        raise learning_observer.exceptions.SuspiciousOperation(
            "We only handle Google logins. Non-google Provider"
        )

    user = await _google(request)

    if 'user_id' in user:
        await _authorize_user(request, user)

    if user['authorized']:
        url = user['back_to'] or "/"
    else:
        url = "/"

    return aiohttp.web.HTTPFound(url)


async def _google(request):
    '''
    Handle Google login
    '''
    if 'error' in request.query:
        return {}

    common_params = {
        'client_id': settings.settings['auth']['google-oauth']['web']['client_id'],
        'redirect_uri': "https://writing.hopto.org/auth/login/google",
    }

    # Step 1: redirect to get code
    if 'code' not in request.query:
        url = 'https://accounts.google.com/o/oauth2/auth'
        params = common_params.copy()
        params.update({
            'response_type': 'code',
            'scope': (
                'https://www.googleapis.com/auth/userinfo.profile'
                ' https://www.googleapis.com/auth/userinfo.email'
                ' https://www.googleapis.com/auth/classroom.courses.readonly'
                ' https://www.googleapis.com/auth/classroom.rosters.readonly'
                ' https://www.googleapis.com/auth/classroom.profile.emails'
                ' https://www.googleapis.com/auth/classroom.profile.photos'
            ),
        })
        if 'back_to' in request.query:
            params['state'] = request.query['back_to']
        url = yarl.URL(url).with_query(params)
        raise aiohttp.web.HTTPFound(url)

    # Step 2: get access token
    url = 'https://accounts.google.com/o/oauth2/token'
    params = common_params.copy()
    params.update({
        'client_secret': settings.settings['auth']['google-oauth']['web']['client_secret'],
        'code': request.query['code'],
        'grant_type': 'authorization_code',
    })
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        async with client.post(url, data=params) as resp:
            data = await resp.json()
        assert 'access_token' in data, data

        # get user profile
        headers = {'Authorization': 'Bearer ' + data['access_token']}
        session = await aiohttp_session.get_session(request)
        session["auth_headers"] = headers
        request["auth_headers"] = headers

        # Old G+ URL that's no longer supported.
        url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        async with client.get(url, headers=headers) as resp:
            profile = await resp.json()

    return {
        'user_id': profile['id'],
        'email': profile['email'],
        'name': profile['given_name'],
        'family_name': profile['family_name'],
        'back_to': request.query.get('state'),
        'picture': profile['picture'],
        # TODO: Should this be immediate?
        'authorized': await verify_teacher_account(profile['id'], profile['email'])
    }
