'''
Helper utility to help manage paths. We'd like to abstract this out so that the tool can work in:

1) Deployed settings
2) pip installs
3) Development mode
... etc.

This abstracts out finding files and directories. Eventually, we'd
like to be able to search for packages looking at:

- Relative directories (e.g. when developing)
- Static directories (e.g. /etc/, /var/log/, etc.)
- Config file
- pkg_resources
- Command-line parameters

It makes sense to put this logic one place.

Should this be merges with settings.py? Let's see how complex this gets.

'''

import os.path

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
print(BASE_PATH)

def config_file():
    '''
    Main configuration file
    '''
    p = os.path.join(os.path.dirname(BASE_PATH), 'creds.yaml')
    print(p)
    return p

def data(filename=None):
    '''
    File from the static data directory. No parameters: data directory.
    '''
    p = os.path.join(BASE_PATH, 'static_data')
    if filename is not None:
        p = os.path.join(p, filename)
    return p

def logs(filename=None):
    '''
    Log fle. No parameters: log directory.
    '''
    p = os.path.join(BASE_PATH, 'logs')
    if filename is not None:
        p = os.path.join(p, filename)
    print(p)
    return p

def static(filename=None):
    p = os.path.join(BASE_PATH, 'static')
    if filename is not None:
        p = os.path.join(p, filename)
    print(p)
    return p


def third_party(filename=None):
    p = static('3rd_party')
    if filename is not None:
        p = os.path.join(p, filename)
    print(p)
    return p
