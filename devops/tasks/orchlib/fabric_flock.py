'''
These are baseline script to help orchestrate a flock of machines
via ssh. This is a thin wrapper around `fabric`.
'''

import yaml
import fabric

import orchlib.config


def machine_pool():
    '''
    Return a line formatted for Fabric with a list of hosts:

    >>> "host1 host2 host3"

    This is kind of obsolete, since this should be queried from
    the provider
    '''
    def clean_line(line):
        # Remove comments
        if line.find("#") != -1:
            line = line[:line.find("#")]
        # Remove whitespace
        return line.strip()

    lines = open("settings/HOSTS").readlines()
    cleaned = [clean_line(h) for h in lines]
    host_string = " ".join(h for h in cleaned if len(h) > 0)
    return host_string


def group_from_poolstring(pool):
    return fabric.SerialGroup(
        pool,
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

