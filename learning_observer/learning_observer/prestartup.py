'''
This is at the edge of dev-ops and operations. We would like to:
- Confirm that the system is ready to run the Learning Observer.
- Create directories for log files, etc.
- Validate the teacher list file.
- Validate the configuration file exists.
- Download any missing 3rd party files.
- Confirm their integrity.
- Create any directories that don't exist.
'''

import hashlib
import os
import os.path
import shutil
import sys

import learning_observer.paths as paths

import learning_observer.module_loader as module_loader


class StartupCheck(Exception):
    '''
    Exception to be raised when a startup check fails.
    '''
    pass


# These are directories we'd like created on startup. At the moment,
# they're for different types of log files.
directories = {
    'logs': {'path': paths.logs()},
    'startup logs': {'path': paths.logs('startup')},
    'AJAX logs': {'path': paths.logs('ajax')},
    '3rd party': {'path': paths.third_party()}
}


def make_blank_dirs(directories):
    '''
    Create any directories that don't exist for e.g. log files and
    similar.
    '''
    for d in directories:
        dirpath = directories[d]['path']
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
            print("Made {dirname} directory in {dirpath}".format(
                dirname=d,
                dirpath=dirpath
            ))


def validate_teacher_list():
    '''
    Validate the teacher list file. This is a YAML file that contains
    a list of teachers authorized to use the Learning Observer.
    '''
    if not os.path.exists(paths.data("teachers.yaml")):
        shutil.copyfile(
            paths.data("teachers.yaml.template"),
            paths.data("teachers.yaml")
        )
        raise StartupCheck("Created a blank teachers file: static_data/teachers.yaml\n"
              "Populate it with teacher accounts.")


def validate_config_file():
    '''
    Validate the configuration file exists. If not, explain how to
    create a configuration file based on the example file.
    '''
    if not os.path.exists(paths.config_file()):
        raise StartupCheck("""
            Copy creds.yaml.sample into the top-level directory:
            cp creds.yaml.sample ../creds.yaml
            Fill in the missing fields.
        """)


def download_3rd_party_static(libs):
    '''
    Download any missing third-party files, and confirm their integrity.
    We download only if the file doesn't exist, but confirm integrity
    in both cases.
    '''
    for name in libs:
        url = libs[name]['urls'][0]
        sha = libs[name]['hash']

        filename = paths.third_party(name)
        if not os.path.exists(filename):
            os.system("wget {url} -O {filename} 2> /dev/null".format(
                url=url,
                filename=filename
            ))
            print("Downloaded {name}".format(name=name))
        shahash = hashlib.sha3_512(open(filename, "rb").read()).hexdigest()
        if shahash == sha:
            pass
        # print("File integrity of {name} confirmed!".format(name=filename))
        else:
            # Do we want to os.unlink(filename) or just terminate?
            # Probably just terminate, so we can debug.
            error = "File integrity of {name} failed!\n" \
                    "Expected: {sha}\n" \
                    "Got: {shahash}\n" \
                    "We download 3rd party libraries from the Internet. This error means that ones of\n" \
                    "these files changed. This may indicate a man-in-the-middle attack, that a CDN has\n" \
                    "been compromised, or more prosaically, that one of the files had something like\n" \
                    "a security fix backported. In either way, VERIFY what happened before moving on.\n\n" \
                    "If unsure, please consult with a security expert.".format(
                        name=filename,
                        sha=sha,
                        shahash=shahash
                    )
            raise StartupCheck(error)


STARTUP_CHECKS = []
INIT_FUNCTIONS = []
STARTUP_RAN = False


def additional_checks():
    '''
    Allow modules to register additional checks beyond those defined here.

    We should support asynchronous functions here, but that's a to do. Probably,
    we'd introspect to see whether return values are promises, or have a
    register_sync and a register_async.
    '''
    for check in STARTUP_CHECKS:
        check()
    for init in INIT_FUNCTIONS:
        init()
    STARTUP_RAN = True


def register_startup_check(check):
    '''
    Allow modules to register additional checks beyond those defined here. This
    function takes a function that takes no arguments and returns nothing which
    should run after settings are configured, but before the server starts.
    '''
    if STARTUP_RAN:
        raise StartupCheck(
            "Cannot register additional checks after startup checks have been run."
        )
    STARTUP_CHECKS.append(check)


def register_init_function(init):
    '''
    Allow modules to initialize modules after settings are loaded and startup checks have 
    run. This function takes a function that takes no arguments and returns nothing which
    should run before the server starts.
    '''
    if STARTUP_RAN:
        raise StartupCheck(
            "Cannot register additional checks after startup checks have been run."
        )
    INIT_FUNCTIONS.append(init)


def startup_checks_and_init():
    '''
    Run a series of checks to ensure that the system is ready to run
    the Learning Observer and create any directories that don't exist.
    '''
    make_blank_dirs(directories)
    validate_teacher_list()
    validate_config_file()
    libs = module_loader.third_party()
    download_3rd_party_static(libs)
    additional_checks()
