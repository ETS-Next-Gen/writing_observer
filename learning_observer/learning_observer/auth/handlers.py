'''
Authentication subsystem. Most of this should be moved into utils or this
module should be renamed.
'''


import base64
import json
import sys
import yaml

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


# We need some auth
if 'auth' not in settings.settings:
    print("Please configure auth")

# If we have Google oauth, we need it properly configured.
# TODO: Confirm everything works with Google Oauth missing
if 'google-oauth' in settings.settings['auth']:
    if 'web' not in settings.settings['auth']['google-oauth'] or \
       'client_secret' not in settings.settings['auth']['google-oauth']['web'] or \
       'project_id' not in settings.settings['auth']['google-oauth']['web'] or \
       'client_id' not in settings.settings['auth']['google-oauth']['web'] or \
       isinstance(settings.settings['auth']['google-oauth']['web']['client_secret'], dict) or \
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
