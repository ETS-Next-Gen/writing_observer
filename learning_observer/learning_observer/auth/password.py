'''
Password log-in handler
'''
import bcrypt
import json
import yaml

import aiohttp.web

import learning_observer.auth.handlers
import learning_observer.auth.utils


def password_auth(filename):
    '''
    Authentication handler for logging in with username and password
    based on a password file.

    By placing this in a closure, we eliminate the dependency on
    settings.

    Todo:
    * Flag to load file on startup versus on request
    * Support storing this in a database
    * Log out after time-out from last request

    For convenience, this can be called directly as:

    `curl -X POST \
          -F "username=test_user" \
          -F "password=test_password" \
          http://localhost:8888/23auth/login/password`
    '''
    async def password_auth_handler(request):
        data = await request.post()  # Web form
        body = await request.text()  # AJAX
        if 'username' not in data:
            data = json.loads(body)
        password_data = yaml.safe_load(open(filename))

        # If you run into errors on the line below, you *probably*
        # have a dependency issue. Errors:
        # * AttributeError: module 'bcrypt' has no attribute 'checkpw'
        # * AttributeError: module 'bcrypt._bcrypt' has no attribute 'ffi'
        # Try uninstalling bcrypt and reinstalling / upgrading pi-bcrypt
        #
        # If you run into unicode errors, see if you can debug them. There
        # is randomness about whether we do or don't need to .encode('utf-8').
        #
        # It reliably either works or doesn't, but it doesn't change. If your
        # environment has a happy `bcrypt`, it will keep on working.
        if (data['username'] in password_data['users']
            and bcrypt.checkpw(
                data['password'].encode('utf-8'),
                password_data['users'][data['username']]['password'].encode('utf-8')
        )):
            print("Authorized")
            await learning_observer.auth.utils.update_session_user_info(
                request, {
                    'user_id': "pwd-" + data['username'],
                    'email': "",
                    'name': "",
                    'family_name': "",
                    'picture': "",
                    'authorized': True
                }
            )
            return aiohttp.web.json_response({"status": "authorized"})

        print("Unauthorized")
        await learning_observer.auth.utils.logout(request)
        return aiohttp.web.json_response({"status": "unauthorized"})
    return password_auth_handler
