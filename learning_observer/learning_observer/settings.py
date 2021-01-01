import yaml

import learning_observer.paths


settings = yaml.safe_load(open(learning_observer.paths.config_file()))
