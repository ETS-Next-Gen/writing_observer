'''
This file mostly confirms we have prerequisites for the system to work.

We create a logs directory, grab 3rd party libraries, etc.
'''

import hashlib
import os
import os.path
import shutil
import sys

import paths

import module_loader


# These are directories we'd like created on startup. At the moment,
# they're for different types of log files.
directories = {
    'logs': {'path': paths.logs()},
    'startup logs': {'path': paths.logs('startup')},
    'AJAX logs': {'path': paths.logs('ajax')}
}

for d in directories:
    dirpath = directories[d]['path']
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
        print("Made {dirname} directory in {dirpath}".format(
            dirname=d,
            dirpath=dirpath
        ))

if not os.path.exists(paths.data("teachers.yaml")):
    shutil.copyfile(
        paths.data("teachers.yaml.template"),
        paths.data("teachers.yaml")
    )
    print("Created a blank teachers file: static_data/teachers.yaml\n"
          "Populate it with teacher accounts.")

if not os.path.exists(paths.config_file()):
    print("""
    Copy creds.yaml.sample into the top-level directory:

    cp creds.yaml.sample ../creds.yaml

    Fill in the missing fields.
    """)
    sys.exit(-1)

if not os.path.exists(paths.third_party()):
    os.mkdir(paths.third_party())


# Download any missing third-party files, and confirm their integrity.
# We download only if the file doesn't exist, but confirm integrity in
libs = module_loader.third_party()
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
        print("Incorrect SHA hash. Something odd is going on. DO NOT IGNORE THIS ERROR/WARNING")
        print()
        print("Expected SHA: " + sha)
        print("Actual SHA: " + shahash)
        print()
        print("We download 3rd party libraries from the Internet. This error means that ones of")
        print("these files changed. This may indicate a man-in-the-middle attack, that a CDN has")
        print("been compromised, or more prosaically, that one of the files had something like")
        print("a security fix backported. In either way, VERIFY what happened before moving on.")
        print("If unsure, please consult with a security expert.")
        print()
        print("This error should never happen unless someone is under attack (or there is a")
        print("serious bug).")
        # Do we want to os.unlink(filename) or just terminate?
        # Probably just terminate, so we can debug.
        sys.exit(-1)
        print()
