'''
Install script. Everything is handled in setup.cfg

To set up locally for development, run `python setup.py develop`, in a
virtualenv, preferably.
'''
from setuptools import setup

setup(
    name="wo_classroom_text_highlighter",
    package_data={
        'wo_classroom_text_highlighter': ['assets/*'],
    }
)
