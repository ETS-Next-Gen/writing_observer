'''
Password log-in handler
'''
import bcrypt
import yaml

import aiohttp.web

import learning_observer.auth_handlers

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

    `curl -X POST -F "username=test_user" -F "password=test_password" http://localhost:8888/23auth/login/password`
    '''
    async def password_auth_handler(request):
        data = await request.post()
        password_data = yaml.safe_load(open(filename))
        if data['username'] in password_data['users'] and \
           bcrypt.checkpw(
               data['password'],
               password_data['users'][data['username']]['password']
           ):
            print("Authorized")
            await learning_observer.auth_handlers._authorize_user(
                request, {
                    'user_id': "pwd-"+data['username'],
                    'email': "",
                    'name': "",
                    'family_name': "",
                    'back_to': request.query.get('state'),
                    'picture': "",
                    'authorized': True
                }
            )
            return aiohttp.web.json_response({"status": "authorized"})
        else:
            print("Unauthorized")
            await learning_observer.auth_handlers.logout(request)
            return aiohttp.web.json_response({"status": "unauthorized"})
    return password_auth_handler
