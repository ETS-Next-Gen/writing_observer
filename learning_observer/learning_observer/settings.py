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

    parser.add_argument(
        '--console',
        help='Instead of launching a web server, run a debug console.',
        default=None,
        action='store_true')

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


def match_rule(condition, rule):
    '''Check if a dictionary of conditions match a rule.

    >>> match_rule({'a': 123, 'b': 456}, {'a': 123})
    True
    >>> match_rule({'a': 123, 'b': 456}, {'a': 123, 'c': 789})
    False
    '''
    if all(condition.get(key) == value for key, value in rule['condition'].items()):
        return True
    return False


RULE_PRIORITIES = {
    'school': 1,
    'teacher': 2,
    'course': 3
}


def determine_rule_priority(rule):
    '''Fetches the rule's priority based on the keys in the
    rule's conditional subobject.
    '''
    conditionals = rule['condition'].keys()
    max_priority = max(RULE_PRIORITIES.get(key, 0) for key in conditionals)
    return max_priority


class settingsRuleWrapper(dict):
    '''This is a wrapper to allow the settings dictionary to access
    different layers of a configuration based on rules imposed. The
    base `settings` are treated as the default.
    '''
    def __init__(self, settings, rules):
        self.settings = settings
        self.rules = rules
        super().__init__(settings)

    def get(self, setting, default=None, condition=None):
        # TODO we probably want some way to say no overriding certain settings
        primary_setting = super().get(setting, default)
        if condition is None:
            return primary_setting
        value = self.find_setting_based_on_rule(setting, condition, primary_setting)
        return value

    def find_setting_based_on_rule(self, setting, condition, default):
        '''We iterate over the rules to find any matching items. We
        sort them by priority then iterate over them to find the first
        instance of the `setting` we are trying to locate.
        '''
        rules = []
        for r in self.rules:
            if match_rule(condition, r):
                r['priority'] = determine_rule_priority(r)
                rules.append(r)
        rules = sorted(rules, key=lambda x: x['priority'], reverse=True)
        value = next((r['config'][setting] for r in rules if setting in r['config']), default)
        return value


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

    # TODO read rules in from somewhere
    rules = [{
        'condition': {'teacher': 'john doe', 'school': 'eastview'},
        'config': {'example_setting': 'only-john-doe'}
    },{
        'condition': {'school': 'eastview'},
        'config': {'example_setting': 'all-of-eastview'}
    }]
    settings = settingsRuleWrapper(settings, rules)

    # TODO remove testing code
    default = 'default'
    test = settings.get('example_setting', default=default, condition={'teacher': 'john doe', 'school': 'eastview'})
    print('****')
    print(test)
    print('****')
    test = settings.get('example_setting', default=default, condition={'teacher': 'jane doe', 'school': 'eastview'})
    print('****')
    print(test)
    print('****')

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


class SettingsException(Exception):
    pass


NOT_INITIALIZED_ERROR = \
    """Attempted to access Learning Observer settings before initializing
    them:
    * If you are writing test code, use `offline.init()` for a minimalist
    in-memory debug settings version.
    * If you are running in the main system, you probably have a bug with
    load / initialization order."""


def initialized():
    '''
    Check if we're initialized. If not, raise an exception
    '''
    if settings is None:
        raise SettingsException(
            NOT_INITIALIZED_ERROR
        )
    return True


# Not all of these are guaranteed to work on every branch of the codebase.
AVAILABLE_FEATURE_FLAGS = ['uvloop', 'watchdog', 'auth_headers_page', 'merkle', 'save_google_ajax', 'use_google_ajax']


def feature_flag(flag):
    '''
    Return `None` if the given feature flag is disabled.

    Returns the value of the feature flag if it is enabled.
    '''
    initialized()
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
    initialized()
    module_settings = settings.get(
        'modules', {}
    ).get(module_name, None)
    if setting is None:
        return module_settings
    if module_settings is not None:
        return module_settings.get(setting, default)
    return default
