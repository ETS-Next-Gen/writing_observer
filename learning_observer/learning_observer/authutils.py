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
