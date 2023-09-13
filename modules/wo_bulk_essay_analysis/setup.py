'''
Rather minimalistic install script. To install, run `python
setup.py develop` or just install via requirements.txt
'''

from setuptools import setup, find_packages

setup(
    name="wo_bulk_essay_analysis",
    package_data={
        'wo_bulk_essay_analysis': ['assets/*'],
    }
)
