'''
Helper utility to help manage paths. We'd like to abstract this out so that the tool can work in:

1) Deployed settings
2) pip installs
3) Development mode
... etc.
'''

import os.path

BASE_PATH = os.path.dirname(__file__)
print(BASE_PATH)

def config_file():
    pass

def data():
    p = os.path.join(BASE_PATH, 'static_data')
    return p

def logs():
    p = os.path.join(BASE_PATH, 'logs')
    return p
