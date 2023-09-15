'''
Install script. Everything is handled in setup.cfg

To set up locally for development, run `python setup.py develop`, in a
virtualenv, preferably.
'''

from setuptools import setup
from setuptools.command.develop import develop as _develop

import os
import subprocess
import sys

my_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.abspath(os.path.join(my_path, os.pardir))
req_path = os.path.join(parent_path, 'requirements.txt')
awe_path = os.path.join(parent_path, 'awe_requirements.txt')
wo_path = os.path.join(parent_path, 'wo_requirements.txt')


def clean_requirements(filename):
    file_path = os.path.join(parent_path, filename)
    requirements = [s.strip() for s in open(file_path).readlines() if len(s) > 1]
    return requirements


new_path = '/'.join(sys.executable.split('/')[:-1])
current_path = os.environ['PATH']
modified_env = {'PATH': f'{new_path}{os.pathsep}{current_path}'}


class LOInstall(_develop):
    '''
    LO_dash_react_components relies on Dash to be installed.
    To ensure Dash (and any other downstream dependencies) are resolved first,
    we install LODRC after the install_requires
    '''
    def run(self):
        _develop.run(self)
        subprocess.run(['pip', 'install', '-v', '-e', 'git+https://github.com/ETS-Next-Gen/writing_observer.git#egg=lo_dash_react_components&subdirectory=modules/lo_dash_react_components'], env=modified_env)


setup(
    install_requires=clean_requirements(req_path),
    extras_require={
        "wo": clean_requirements(wo_path),
        "awe": clean_requirements(awe_path)
    },
    cmdclass={
        'develop': LOInstall
    }
)
