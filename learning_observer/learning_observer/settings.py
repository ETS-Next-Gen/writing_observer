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


# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)


args = None
parser = None


def parse_and_validate_arguments():
    '''
    Parse and validate command line arguments; for now, just the
    configuration file location.
    '''
    global args, parser
    parser = argparse.ArgumentParser(
        description='The Learning Observer',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--config-file',
        help='Specify an alternative configuration file',
        default=learning_observer.paths.config_file())

    parser.add_argument(
        '--watchdog',
        help='Run in watchdog mode. This will restart on file changes.',
        default=None)

    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        raise FileNotFoundError(
            "Configuration file not found: {config_file}\n"
            "\n"
            "Copy the example file into:\n"
            "{config_file}\n"
            "And then continue setup\n"
            "The command is probably:\n"
            "cp {sourcedir}/creds.yaml.example {dest}".format(
                sourcedir=os.path.dirname(os.path.abspath(__file__)),
                dest=args.config_file,
                config_file=args.config_file
            )
        )
    return args


# DEV = Development, with full debugging
# DEPLOY = Running on a server, with good performance
# INTERACTIVE = Processing data offline
RUN_MODES = enum.Enum('RUN_MODES', 'DEV DEPLOY INTERACTIVE')
RUN_MODE = None

settings = None


def load_settings(config):
    '''
    Load the settings file and return a dictionary of settings. Also:
    - Allow a stub data path
    - Select the run mode
    - Set up location of module repositories, if overridden in the config

    This is a wrapper around `yaml.safe_load()` so we can do some validation,
    error handling, and postprocessing.

    :param config: The configuration file to load, or a dictionary of settings
    :return: A dictionary of settings

    We can work from a dictionary rather than config file because we want to
    be able to use pieces of the Learning Observer in scripts and tests, where
    we don't need a full config.
    '''
    global settings

    if isinstance(config, str):
        with open(config, 'r') as f:
            settings = yaml.safe_load(f)
    elif isinstance(config, dict):
        settings = config
    else:
        raise AttributeError("Invalid settings file")

    # For testing and similar, we'd like to be able to have alternative data
    # paths
    if 'data_path' in settings:
        learning_observer.paths.override_data_path(settings['data_path'])

    # Development versus deployment. This is helpful for logging, verbose
    # output, etc.
    global RUN_MODE
    if settings['config']['run_mode'] == 'dev':
        RUN_MODE = RUN_MODES.DEV
    elif settings['config']['run_mode'] == 'deploy':
        RUN_MODE = RUN_MODES.DEPLOY
    elif settings['config']['run_mode'] == 'interactive':
        RUN_MODE = RUN_MODES.INTERACTIVE
    else:
        raise ValueError("Configuration setting for run_mode must be either 'dev', 'deploy', or 'interactive'")

    if 'repos' in settings:
        for repo in settings['repos']:
            # In the future, we might allow dicts if we e.g. want more metadata
            if isinstance(settings['repos'][repo], str):
                learning_observer.paths.register_repo(repo, settings['repos'][repo])
            elif isinstance(settings['repos'][repo], dict):
                # HACK. We should figure out where to stick this. This does not belong in paths
                debug_working = settings['repos'][repo].get("debug_working", None)

                learning_observer.paths.register_repo(
                    repo,
                    settings['repos'][repo]['path'],
                    debug_working=debug_working
                )
            else:
                raise ValueError("settings.repos.{repo} should be a string or a dict. Please fix the settings file.".format(repo=repo))

    return settings


# Not all of these are guaranteed to work on every branch of the codebase.
AVAILABLE_FEATURE_FLAGS = ['uvloop', 'watchdog', 'auth_headers_page', 'merkle', 'save_google_ajax', 'use_google_ajax']


def feature_flag(flag):
    '''
    Return `None` if the given feature flag is disabled.

    Returns the value of the feature flag if it is enabled.
    '''
    if flag not in AVAILABLE_FEATURE_FLAGS:
        raise ValueError(
            f"Unknown feature flag: {flag}"
            f"Available feature flags: {AVAILABLE_FEATURE_FLAGS}"
        )

    flag = settings.get(
        'feature_flags', {}
    ).get(flag, None)

    # The feature flag is disabled if it is False, None, or omitted
    if flag is False:
        return None

    return flag


def module_setting(module_name, setting=None, default=None):
    '''
    Return the settings for a specific module.

    Optionally, can be passed a specific setting.

    Returns `default` if no setting (or `None` if not set)
    '''
    module_settings = settings.get(
        'modules', {}
    ).get(module_name, None)
    if setting is None:
        return module_settings
    if module_settings is not None:
        return module_settings.get(setting, default)
    return default
