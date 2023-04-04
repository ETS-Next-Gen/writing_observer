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


async def verify_teacher_account(user_id, email):
    '''
    Confirm the teacher is registered with the system. Eventually, we will want
    3 versions of this:
    * Always true (open system)
    * Text file backed (pilots, small deploys)
    * Database-backed (large-scale deploys)

    For now, we have the file-backed version
    '''
    teachers = yaml.safe_load(open(learning_observer.paths.data("teachers.yaml")))
    if email not in teachers:
        # email is untrusted; repr prevents injection of newlines
        debug_log("Email not found in teachers", repr(email))
        return False
    if teachers[email]["google_id"] != user_id:
        # user_id is untrusted; repr prevents injection of newlines
        debug_log("Non-matching Google ID", teachers[email]["google_id"], repr(user_id))
        return False
    debug_log("Teacher account verified")
    return True


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


async def logout(request):
    '''
    Log the user out
    '''
    session = await aiohttp_session.get_session(request)
    session.pop("user", None)
    session.pop("auth_headers", None)
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


def admin(func):
    '''
    Decorator to mark a view as an admin view.

    This should be moved to the auth/auth framework, and have more
    granular levels (e.g. teachers and sys-admins). We probably don't
    want a full ACL scheme (which overcomplicates things), but we will
    want to think through auth/auth.
    '''
    @functools.wraps(func)
    def wrapper(request):
        if learning_observer.settings.settings['auth'].get("test_case_insecure", False):
            return func(request)
        if 'user' in request and \
           request['user'] is not None and \
           'authorized' in request['user'] and \
           request['user']['authorized']:
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


# Decorator
#
# For now, we don't have seperate teacher and admin accounts.
teacher = admin
