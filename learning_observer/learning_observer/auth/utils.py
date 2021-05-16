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

import aiohttp.web


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
        print("Error handling:", google_id)
        raise


def fernet_key(secret_string):
    '''
    Generate key for our cookie storage based on the `session_secret`
    in our config file.
    '''
    md5_hash = hashlib.md5()
    md5_hash.update(secret_string.encode('utf-8'))
    return md5_hash.hexdigest().encode('utf-8')


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
        if 'user' in request and \
           request['user'] is not None and \
           'authorized' in request['user'] and \
           request['user']['authorized']:
            return func(request)
        # Else, if unauthorized
        raise aiohttp.web.HTTPUnauthorized(text="Please log in")
    return wrapper


# Decorator
#
# For now, we don't have seperate teacher and admin accounts.
teacher = admin
