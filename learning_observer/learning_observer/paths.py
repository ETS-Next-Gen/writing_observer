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


def base_path():
    '''
    Should NOT be used, except by filesystem_state. Use one of the helpers below.
    '''
    return BASE_PATH


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


GIT_REPO_ARCHIVE = {}


def repo(reponame=None):
    '''
    We keep downloaded `git` repos from modules in the static data
    directory. This returns the base path of a `git` repo.

    `git` repos may also be stored other places.
    '''
    if reponame in GIT_REPO_ARCHIVE:
        return GIT_REPO_ARCHIVE[reponame]['PATH']

    p = data("repos")
    if reponame is not None:
        p = os.path.join(data, reponame)
    return p


def register_repo(reponame, path):
    '''
    Let the system know the location of a repo on the local drive
    '''
    pass


def logs(filename=None):
    '''
    Log file. No parameters: log directory.
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
