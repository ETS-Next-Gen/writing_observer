'''
Install script. Everything is handled in setup.cfg

To set up locally for development, run `python setup.py develop`, in a
virtualenv, preferably.
'''

from setuptools import setup
import os

my_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.abspath(os.path.join(my_path, os.pardir))
req_path = os.path.join(parent_path, 'requirements.txt')
awe_path = os.path.join(parent_path, 'awe_requirements.txt')

def clean_requirements(filename):
    file_path = os.path.join(parent_path, filename)
    requirements = [s.split("#")[0].strip() for s in open(file_path).readlines() if len(s)>1]
    return requirements

setup(
    install_requires = clean_requirements(req_path),
    extras_require = {
        "awe": clean_requirements(awe_path)
    }
)
