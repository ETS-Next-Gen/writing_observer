'''
This file should contain handlers and all the other aio_http stuff for auth/auth.

We should give it a better name, since it also contains middlewares
'''

import base64
import json

import aiohttp
import aiohttp.web
import aiohttp_session

import learning_observer.auth.utils


async def logout_handler(request):
    """
    Handles sign out. This is generic - does not depend on which
    log-in method is used (password, social, etc.)
    """
    session = await learning_observer.auth.utils.logout(request)
    return aiohttp.web.HTTPFound("/")  # TODO: Make a proper logout page


async def user_info_handler(request):
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
