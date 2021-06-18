'''
System Configuration
====================

This is just a wrapper to load out configuration YAML file from disk.

At some point, it might make sense to make this a thicker wrapper, so
we can have multiple configuration files with includes. As is, we have
credentials in the same place as module configuration, which is not
ideal.
'''

import argparse
import enum
import os.path
import sys

import yaml

import learning_observer.paths


print("Startup: Loading settings file")

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)

parser = argparse.ArgumentParser(
    description='The Learning Observer',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    '--config-file',
    help='Specify an alternative configuration file',
    default=learning_observer.paths.config_file())

args = parser.parse_args()

if not os.path.exists(args.config_file):
    print("Missing settings file")
    print("Copy the example file into:")
    print(args.config_file)
    print("And then continue setup")
    print()
    print("The command is probably:")
    print("cp {sourcedir}/creds.yaml.example {dest}".format(
        sourcedir=os.path.dirname(os.path.abspath(__file__)),
        dest=args.config_file
    ))
    sys.exit(-1)

settings = yaml.safe_load(open(args.config_file))

# For testing and similar, we'd like to be able to have alternative data
# paths
if 'data_path' in settings:
    learning_observer.paths.override_data_path(settings['data_path'])

RUN_MODES = enum.Enum('RUN_MODES', 'DEV DEPLOY')

RUN_MODE = None

if 'config' not in settings or 'run_mode' not in settings['config']:
    print("Configuration file must specify a run mode (dev versus deploy)")
    sys.exit(-1)

if settings['config']['run_mode'] == 'dev':
    RUN_MODE = RUN_MODES.DEV
elif settings['config']['run_mode'] == 'deploy':
    RUN_MODE = RUN_MODES.DEPLOY
else:
    print("Configuration setting for run_mode must be either 'dev' or 'deploy'")
    sys.exit(-1)

if 'repos' in settings:
    for repo in settings['repos']:
        # In the future, we might allow dicts if we e.g. want more metadata
        if isinstance(settings['repos'][repo], str):
            learning_observer.paths.register_repo(repo, settings['repos'][repo])
        elif isinstance(settings['repos'][repo], dict):
            # HACK. We should figure out where to stick this. This does not belong in paths
            debug_working = settings['repos'][repo].get("debug-working", False)

            learning_observer.paths.register_repo(repo, settings['repos'][repo]['path'], debug_working=debug_working)
        else:
            print("settings.repos.{repo} should be a string or a dict. Please fix the settings file.")
            sys.exit(-1)
