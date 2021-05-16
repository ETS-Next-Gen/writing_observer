'''
Handle HTTP basic authentication

Curiously, the Wikipedia article is the best reference on this.

We would like to support two modes of operation:

1) Rely on nginx
2) Rely on our own password file

For now, we only support #1. We do not verify passwords, and let
our web server do it for us.

Well, technically, for now we support neither since this file is IN
DEVELOPMENT, and NOT YET WORKING.
'''
import base64
import json
import yaml

import bcrypt

import aiohttp.web

import learning_observer.auth.handlers

def http_basic_auth(filename=None):
    '''
    Takes a password file. For now, this is not fully implemented / tested
    '''
    if filename is not None:
        raise aiohttp.web.HTTPNotImplemented(body="HTTP auth should be handled by the web server.")

    async def password_auth_handler(request):
        auth_header = request.headers['Authorization']
        if not auth_header.startswith("Basic "):
            raise aiohttp.web.HTTPBadRequest("Malformed header authenticating.")
        split_header = auth_header.split(" ")
        if len(split_header) != 2:
            raise aiohttp.web.HTTPBadRequest("Malformed header authenticating.")
        decoded_header = base64.b64decode(split_header[1]).decode('utf-8')
        (username, password) = decoded_header.split(":")

        # TODO:
        # * Confirm filesystem authentication code below works
        # * Write code to add header asking client to authorize
        if filename is not None:
            # We should check this codepath before we run it....
            raise aiohttp.web.HTTPNotImplemented(body="Password file http basic unimplemented.")
            password_data = yaml.safe_load(open(filename))
            if not data['username'] in password_data['users'] or \
               not bcrypt.checkpw(
                   password,
                   password_data['users'][username]['password']
               ):
                raise HTTPUnauthorized("Invalid username / password")

        # TODO: We should sanitize the username.
        # That's a bit of paranoia, but just in case something goes wrong in nginx or similar
        await learning_observer.auth.utils.update_session_user_info(
            request, {
                'user_id': "httpauth-"+username,
                'email': "",
                'name': "",
                'family_name': "",
                'picture': "",
                'authorized': True
            }
        )
        return aiohttp.web.json_response({"status": "authorized"})
    return password_auth_handler
