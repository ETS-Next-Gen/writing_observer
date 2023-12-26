'''
Authutils
=========

We will need to support IDs from multiple systems. These are helper
functions to convert IDs. For example, we would convert a Google ID
like `72635729500910017892163494291` to
`gc-72635729500910017892163494291`. In the process, we also
double-check to make sure these are well-formed (in the above case, by
converting to int and back).

The whole auth system ought to be reorganized at some point.
'''

import hashlib
import functools

import bcrypt
import yaml

import aiohttp.web
import aiohttp_session

import learning_observer.paths

from learning_observer.log_event import debug_log
from . import roles

# TODO this is originally defined in a file that
# imports this one, so we are unable to import it.
# We should move the constant and import this instead.
IMPERSONATING_AS = 'impersonating_as'


def google_id_to_user_id(google_id):
    '''
    Convert a Google ID like:
    `72635729500910017892163494291`
    to:
    `gc-72635729500910017892163494291`
    '''
    try:
        return "gc-" + str(int(google_id))
    except ValueError:
        debug_log("Error handling:", google_id)
        raise


def fernet_key(secret_string):
    '''
    Generate key for our cookie storage based on the `session_secret`
    in our config file.
    '''
    md5_hash = hashlib.md5()
    md5_hash.update(secret_string.encode('utf-8'))
    return md5_hash.hexdigest().encode('utf-8')


async def verify_role(user_id, email):
    '''
    Confirm the user is registered with the system. Eventually, we will want
    3 versions of this:
    * Always true (open system)
    * Text file backed (pilots, small deploys)
    * Database-backed (large-scale deploys)
    '''
    for k in roles.USER_FILES.keys():
        users = yaml.safe_load(open(learning_observer.paths.data(roles.USER_FILES[k])))
        if email not in users:
            # email is untrusted; repr prevents injection of newlines
            debug_log(f"Email not found in {roles.USER_FILES[k]}", repr(email))
            continue
        if users[email]["google_id"] != user_id:
            # user_id is untrusted; repr prevents injection of newlines
            debug_log(f"Non-matching Google ID in {roles.USER_FILES[k]}", users[email]["google_id"], repr(user_id))
            continue
        debug_log(f"{k} account verified")
        return k
    return roles.ROLES.STUDENT


async def update_session_user_info(request, user):
    """
    This will update the (encrypted) user session with the user's
    identity, and whether they are authorized. This is typically used
    to log a user into our session.

    :param request: web request.
    :param user_id: provider's user ID (e.g., Google ID).

    """
    session = await aiohttp_session.get_session(request)
    session["user"] = user


async def get_active_user(request):
    '''
    Fetch current impersonated user or self from session
    '''
    session = await aiohttp_session.get_session(request)
    if IMPERSONATING_AS in session:
        return session[IMPERSONATING_AS]
    return session['user']


async def logout(request):
    '''
    Log the user out
    '''
    session = await aiohttp_session.get_session(request)
    session.pop("user", None)
    session.pop("auth_headers", None)
    session.pop(IMPERSONATING_AS, None)
    request['user'] = None


class InvalidUsername(aiohttp.web.HTTPUnauthorized):
    '''
    Raised when we try to verify an invalid username

    We have custom exceptions since:
    * We'd like the user to see the same error whether for
      invalid username or password
    * We'd like to programmatically be able to distinguish the
      two
    '''


class InvalidPassword(aiohttp.web.HTTPUnauthorized):
    '''
    Raised when we try to verify an invalid password
    '''


async def verify_password(filename, username, password):
    '''
    Check if user is in password file. If so, return associated user
    information as a JSON dictionary. If not, raise an exception.
    '''
    password_data = yaml.safe_load(open(filename))
    if username not in password_data['users']:
        raise InvalidUsername(text="Invalid username or password")
    user_data = password_data['users'][username]
    if not bcrypt.checkpw(
            password,
            user_data['password']
    ):
        raise InvalidUsername(text="Invalid username or password")
    del user_data['password']
    return user_data

# Account decorators below.
#
# We don't want a complex authentication scheme. In the short term,
# we plan to have teacher, student, and admin accounts.
#
# In the long term, we will probably want a little more, but not full ACLs.
def _role_required(role):
    '''Returns a decorator for viewing pages that require the passed
    in `role`. The role is stored in the user object under `user.role`.
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request):
            if learning_observer.settings.settings['auth'].get("test_case_insecure", False):
                return func(request)
            '''TODO evaluate how we should be using `role` with the
            `authorized` key.

            `authorized` is how the auth workflow used to work. This
            was set to True for teachers/admins and false otherwise.
            With the new inclusion of `role`, I'm not sure we need to
            use `authorized` anymore.

            When this is resolved, we need to update each source of
            auth in our code (e.g. password, http_basic, google, etc.)
            '''
            if 'user' in request and \
            request['user'] is not None and \
            'authorized' in request['user'] and \
            request['user']['authorized'] and \
            'role' in request['user'] and \
            (request['user']['role'] == role or request['user']['role'] == roles.ROLES.ADMIN):
                return func(request)
            # Else, if unauthorized
            # send user to login page /
            # there may be a slight oddball with the url hash being
            # included after the location updates
            response = aiohttp.web.Response(status=302)
            redirect_url = '/'
            response.headers['Location'] = redirect_url
            raise aiohttp.web.HTTPFound(location=redirect_url, headers=response.headers)
        return wrapper
    return decorator


teacher = _role_required(roles.ROLES.TEACHER)
admin = _role_required(roles.ROLES.ADMIN)
