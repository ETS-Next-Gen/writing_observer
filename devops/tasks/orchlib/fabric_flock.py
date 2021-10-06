'''
These are baseline script to help orchestrate a flock of machines
via ssh. This is a thin wrapper around `fabric`.
'''

import yaml
import fabric

import orchlib.config


def machine_group(*pool):
    return fabric.SerialGroup(
        *pool,
        user=orchlib.config.creds['user'],
        connect_kwargs={"key_filename": orchlib.config.creds['key_filename']}
    )


def connection_group(pool = None):
    '''
    Return a Fabric connection group
    '''
    if pool is None:
        pool = machine_pool()

    return fabric.SerialGroup(
        pool,
        user=orchlib.config.creds['user'],
        connect_kwargs={"key_filename": orchlib.config.creds['key_filename']}
    )

