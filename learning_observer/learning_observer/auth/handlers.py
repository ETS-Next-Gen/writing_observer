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
import learning_observer.auth.http_basic
import learning_observer.settings

import learning_observer.graphics_helpers

import names


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
    if request['user'] is not None:
        userinfo = {
            "name": request['user']['name'],
            "picture": request['user']['picture'],
            "authorized": request['user']['authorized'],
            "google_id": request['user']['user_id'],
            "email": request['user']['email']
        }
    elif (learning_observer.auth.http_basic.http_auth_middleware_enabled()
          and learning_observer.auth.http_basic.has_http_auth_headers(request)):
        # This is a TODO
        userinfo = None
    else:
        userinfo = None

    # Short circuit for test cases without logging in.
    # THIS SHOULD NEVER BE ENABLED ON A LIVE SERVER
    if userinfo is None and learning_observer.settings.settings['auth'].get("test-case-insecure", False):
        userinfo = {
            "name": "Test Case",
            "picture": "testcase.jpg",
            "authorized": True,
            "google_id": 12345,
            "email": "testcase@localhost"
        }

    # Short circuit for demos, cog-labs, development, etc.
    # This should not be enabled on long-running live server, beyond spinning one up
    # for a demo or something.
    #
    # In contrast to the above, this assigns a dummy name and similar. That's bad for
    # testing, where we want determinism, but it's good for demos.
    def name_to_email(name):
        '''
        Convert a name to an email address.

        Args:
            name (str): The name to convert.

        Returns:
            str: The email address.

        Example: "John Doe" -> "jdoe@localhost"
        '''
        name = name.split()
        return name[0][0].lower() + name[-1].lower() + "@localhost"

    if userinfo is None and learning_observer.settings.settings['auth'].get("demo-insecure", False):
        name = names.get_full_name()

        userinfo = {
            "name": full_name,
            "picture": "demo.jpg",
            "authorized": True,
            "google_id": random.randint(10000, 99999),
            "email": name_to_email(full_name)
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


def serve_user_icon(request):
    '''
    Serve a user's default icon:
    * A user's icon if available.
    * An SVG of initials if no other icon is available.
    * A default icon if no other icon is available.

    Args:
        request (aiohttp.web.Request): The request object.

    Returns:
        aiohttp.web.Response: The response object.
    '''

    # Good idea once we have a good icon
    # if request['user'] is None:
    #    return aiohttp.web.FileResponse(
    #        learning_observer.settings.settings['auth']['default-icon']
    #    )

    # In the future, we might want something along the lines of:
    # if 'picture' in request['user']:
    #    return aiohttp.web.FileResponse(
    #        request['user']['picture']
    #    )
    # We don't do this now -- we encode the URL and don't call this function
    # if we have a picture -- since we often serve avatars from Google.
    print(request)
    print(request['user'])

    user = request.get('user', {})
    if user is None:
        user = {}
    name = user.get('name', None)

    return aiohttp.web.Response(
        body=learning_observer.graphics_helpers.default_user_icon(name),
        content_type="image/svg+xml"
    )
