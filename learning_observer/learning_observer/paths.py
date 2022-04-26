'''
Path hierarchy
==============

Helper utility to help manage paths. We'd like to abstract out path
configurations so that the tool can work in:

1. Deployed settings
2. pip installs
3. Development mode

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
import sys


BASE_PATH = os.path.abspath(os.path.dirname(__file__))


# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportErrror("Please use fully-qualified imports")
    sys.exit(-1)


def base_path():
    '''
    Should NOT be used, except by filesystem_state. Use one of the helpers below.
    '''
    return BASE_PATH


def config_file():
    '''
    Main configuration file
    '''
    pathname = os.path.join(os.path.dirname(BASE_PATH), 'creds.yaml')
    return pathname


DATA_PATH_OVERRIDE = None


def override_data_path(new_path):
    '''
    We'd like to be able to serve data files from alternative
    locations, especially for testing
    '''
    global DATA_PATH_OVERRIDE
    if not new_path.startswith("/"):
        DATA_PATH_OVERRIDE = os.path.join(base_path(), new_path)
    else:
        DATA_PATH_OVERRIDE = new_path


def data(filename=None):
    '''
    File from the static data directory. No parameters: data directory.
    '''
    pathname = os.path.join(BASE_PATH, 'static_data')
    if DATA_PATH_OVERRIDE is not None:
        pathname = DATA_PATH_OVERRIDE
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


GIT_REPO_ARCHIVE = {}


def repo(reponame=None):
    '''
    We keep downloaded `git` repos from modules in the static data
    directory. This returns the base path of a `git` repo.

    `git` repos may also be stored other places.
    '''
    if reponame in GIT_REPO_ARCHIVE:
        return GIT_REPO_ARCHIVE[reponame]['PATH']
    pathname = data("repos")
    if reponame is not None:
        pathname = os.path.join(pathname, reponame)
    return pathname


def repo_debug_working_hack(reponame):
    '''
    For debugging, we want to allow serving from the git working dir.

    Just not like this.... We should do the merge in settings.py or
    module_loader, or somewhere else.
    '''
    if reponame in GIT_REPO_ARCHIVE and 'DEBUG_WORKING' in GIT_REPO_ARCHIVE[reponame]:
        return GIT_REPO_ARCHIVE[reponame]['DEBUG_WORKING']
    return False


def register_repo(reponame, path, debug_working):
    '''
    Let the system know the location of a repo on the local drive

    `debug_working` is a HACK. The setting is fine, but this does
    not belong in paths.py
    '''
    GIT_REPO_ARCHIVE[reponame] = {
        "PATH": path,
        "DEBUG_WORKING": debug_working
    }


def logs(filename=None):
    '''
    Log file. No parameters: log directory.
    '''
    pathname = os.path.join(BASE_PATH, 'logs')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


def static(filename=None):
    '''
    This is where we store and serve our own static files
    from. Ideally, our web server should serve these for us, but for
    development and small-scale deploys, it's convenient to be able to
    do it ourselves too.
    '''
    pathname = os.path.join(BASE_PATH, 'static')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname


def third_party(filename=None):
    '''
    This is where we download 3rd party Javascript, CSS, and similar
    files to (e.g., D3, Bulma, etc.)
    '''
    pathname = static('3rd_party')
    if filename is not None:
        pathname = os.path.join(pathname, filename)
    return pathname
