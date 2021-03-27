import enum
import yaml
import sys

import learning_observer.paths


settings = yaml.safe_load(open(learning_observer.paths.config_file()))

RUN_MODE = enum.Enum('RUN_MODE', 'DEV DEPLOY')

run_mode = None

if 'config' not in settings or 'run_mode' not in settings['config']:
    print("Configuration file must specify a run mode (dev versus deploy)")
    sys.exit(-1)

if settings['config']['run_mode'] == 'dev':
    run_mode = RUN_MODE.DEV
elif settings['config']['run_mode'] == 'deploy':
    run_mode = RUN_MODE.DEPLOY
else:
    print("Configuration setting for run_mode must be either 'dev' or 'deploy'")
    sys.exit(-1)
