'''
Install script. Everything is handled in setup.cfg

To set up locally for development, run `python setup.py develop`, in a
virtualenv, preferably.
'''

from setuptools import setup
import os

my_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.abspath(os.path.join(my_path, os.pardir))
file_path = os.path.join(parent_path, 'requirements.txt')

requirements = [s.split("#")[0].strip() for s in open(file_path).readlines() if len(s)>1]

setup(
    install_requires = requirements
)
