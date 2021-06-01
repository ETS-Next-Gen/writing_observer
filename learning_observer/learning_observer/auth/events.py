'''
We would like to have multiple means of assigning identity to incoming student events:

- Assigned per-connection
- Header in the events, unverified (e.g. for use during a coglab,
  during quasi-anonymous browser sessions)
- Header in the events, verified from a password file
- HTTP basic auth
- Google oauth
- Etc.

One piece of nuance:

- Some schemes will have a header sent once per connection, with no
  student data (view header, then discard)
- Some schemes will include identity with each event.

We're still figuring out the best ways to do this.
'''

import urllib


async def dummy_auth(metadata):
    '''
    TODO: Replace with real auth
    TODO: Allow configuring auth methods in settings file
    TODO: See about client-side oauth on Chromebooks
    TODO: Allow configuring authentication methods based on event
    type (e.g. require auth for writing, but not for dynamic assessment)

    This is a dummy authentication function. It trusts the metadata in the web
    socket without auth/auth.

    Our thoughts are that the auth metadata ought to contain:
    1. Whether the user was authenticated (`sec` field):
       * `authenticated` -- we trust who they are
       * `unauthenticated` -- we think we know who they are, without security
       * `guest` -- we don't know who they are
    2. Providence: How they were authenticated (if at all), or how we believe
       they are who they are.
    3. `user_id` -- a unique user identifier
    '''
    if 'local_storage' in metadata and 'user-tag' in metadata['local_storage']:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ls-" + metadata['local_storage']['user_tag'],
            'providence': 'lsu'  # local storage, unauthenticated
        }
    elif 'chrome_identity' in metadata:
        gc_uid = authutils.google_id_to_user_id(metadata['chrome_identity']['id'])
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': gc_uid,
            'safe_user_id': gc_uid,
            'providence': 'gcu'  # Google Chrome, unauthenticated
        }
    elif "hash_identity" in metadata:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ts-" + metadata['hash_identity'],
            'providence': 'mch'  # Math contest hash -- toying with plug-in archicture
        }
    elif 'test_framework_fake_identity' in metadata:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ts-" + metadata['test_framework_fake_identity'],
            'providence': 'tsu'  # Test Script, unauthenticated
        }
    else:
        auth_metadata = {
            'sec': 'none',
            'user_id': 'guest',
            'safe_user_id': 'guest',
            'providence': 'guest'
        }

    # This is a bit of encoding logic to generically encode IDs from
    # unknown sources. We want to avoid the problem of Little Bobby
    # Tables (https://xkcd.com/327/).
    #
    # It's not clear this is needed long-term (we put this in when we
    # were using Google emails rather than numeric IDs), but we're
    # keeping it here for now for the test data sources. This just
    # generically sanitizes everything in case we either missed
    # something above, or just want to have a sane default before
    # implementing something fancy.
    #
    # We also want to avoid overlapping UIDs between sources. For
    # example, we don't want an attack where e.g. a user carefully
    # creates an account on one auth provide to collide with a
    # pre-existing account on another auth provider. So we append
    # providence. Note that we don't want to do this twice (so
    # `authutils` does this already for Google)
    if "safe_user_id" not in auth_metadata:
        auth_metadata['safe_user_id'] = "{src}-{uid}".format(
            src=auth_metadata["providence"],
            uid=urllib.parse.quote_plus(
                auth_metadata['user_id'],
                safe='@'  # Keep emails more readable
            )
        )
    return auth_metadata
