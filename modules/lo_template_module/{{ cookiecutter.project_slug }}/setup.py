'''
Install script. Everything is handled in setup.cfg

To set up locally for development, run `python setup.py develop`, in a
virtualenv, preferably.
'''
from setuptools import setup

setup(
    name="{{ cookiecutter.project_slug }}",
    package_data={
        '{{ cookiecutter.project_slug }}': ['assets/*'],
    }
)
