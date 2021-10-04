import os.path

import yaml

creds = yaml.safe_load(open("settings/CREDS.YAML"))

def config_lines(machine_name, file_suffix):
    '''
    Kind of like a smart `open().readlines()` for reading config files.

    Handle paths, prefixes, missing files (return nothing),
    `strip()`ing lines, comments, etc.
    '''
    fn = "config/{mn}-git".format(mn=machine_name)
    if os.path.exists(fn):
        for line in open(fn.readlines()):
            line = line.strip()
            if len(line) > 0:
                yield line
