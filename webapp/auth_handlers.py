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
import aiohttp
import aiohttp.web

import logging
import os.path
import settings
#from aiohttp_jinja2 import template
#from aiohttp.abc import AbstractView
import aiohttp_session
from functools import wraps
from yarl import URL


async def social(request):
    """Handles Google sign in.

    Provider is in `request.match_info['provider']` (currently, only Google)
    """
    if request.match_info['provider'] != 'google':
        raise aiohttp.web.HTTPMethodNotAllowed("We only handle Google logins")

    user = await _google(request)
    print(user)

    if 'user_id' in user:
        # User ID returned in 'data', authorize user.
        await _authorize_user(request, user)
        url = user['back_to'] or "/"
        return aiohttp.web.HTTPFound(url)

    ## Login failed. TODO: Make a proper login failed page.
    return aiohttp.web.HTTPFound("/")


async def _authorize_user(request, user):
     """
     Logs a user in.
     :param request: web request.
     :param user_id: provider's user ID (e.g., Google ID).
     """
     session = await aiohttp_session.get_session(request)
     session["user"] = user


async def logout(request):
    """Handles sign out. This is generic - does not depend on which social ID is logged in
     (Google/Facebook/...)."""
    session = await aiohttp_session.get_session(request)
    session.pop("user", None)
    return aiohttp.web.HTTPFound("/")  ## TODO: Make a proper logout page


@aiohttp.web.middleware
async def auth_middleware(request, handler):
    '''
    Move user into the request

    Save user into a cookie
    '''
    session = await aiohttp_session.get_session(request)
    request['user'] = session.get('user', None)
    resp = await handler(request)
    return resp


async def user_info(request):
    return aiohttp.web.json_response(request['user'])


async def _google(request):
    '''
    Handle Google login
    '''
    if 'error' in request.query:
        return {}

    common_params = {
        'client_id': settings.settings['google-oauth']['web']['client_id'],
        'redirect_uri': "https://writing.hopto.org/auth/login/google",
    }

    # Step 1: redirect to get code
    if 'code' not in request.query:
        url = 'https://accounts.google.com/o/oauth2/auth'
        params = common_params.copy()
        params.update({
            'response_type': 'code',
            'scope': ('https://www.googleapis.com/auth/userinfo.profile'
                      ' https://www.googleapis.com/auth/userinfo.email'),
        })
        if 'back_to' in request.query:
            params['state'] = request.query[back_to]
        url = URL(url).with_query(params)
        raise aiohttp.web.HTTPFound(url)

    # Step 2: get access token
    url = 'https://accounts.google.com/o/oauth2/token'
    params = common_params.copy()
    params.update({
        'client_secret': settings.settings['google-oauth']['web']['client_secret'],
        'code': request.query['code'],
        'grant_type': 'authorization_code',
    })
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        async with client.post(url, data=params) as resp:
            data = await resp.json()
        assert 'access_token' in data, data

        # get user profile
        headers = {'Authorization': 'Bearer ' + data['access_token']}
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
    }


# def login_required(handler):
#     """
#     A handler function decorator that enforces that the user is logged in. If not, redirects to the login page.
#     :param handler: function to decorate.
#     :return: decorated function
#     """
#     @user_to_request
#     @wraps(handler)
#     async def decorator(*args):
#         request = _get_request(args)
#         if not request[cfg.REQUEST_USER_KEY]:
#             return _redirect(_get_login_url(request))
#         return await handler(*args)
#     return decorator


# @user_to_request
# @template('index.html')
# async def index(request):
#     """Web app home page."""
#     return {
#         'auth': {'cfg': cfg},
#         'cur_user': request['user'],
#         'url_for': _url_for,
#     }


# @login_required
# @template('users.html')
# async def users(request):
#     """Handles an example private page that requires logging in."""
#     return {}


