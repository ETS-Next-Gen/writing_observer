import yaml

import paths


settings = yaml.safe_load(open(paths.config_file()))
