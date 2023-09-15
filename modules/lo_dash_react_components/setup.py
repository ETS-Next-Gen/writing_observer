import json
from setuptools import setup
import os
import subprocess
import sys

new_path = '/'.join(sys.executable.split('/')[:-1])
current_path = os.environ['PATH']
modified_env = {'PATH': f'{new_path}{os.pathsep}{current_path}'}

# HACK we need dash installed before we run the NPM commands
# which transform our React components into a Python package
try:
    import dash
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'dash[dev]'])

# TODO make sure the user is using a supported version Node
subprocess.run(['npm', 'install', os.path.abspath(os.path.dirname(__file__))], env=modified_env)
subprocess.run(['npm', 'run', '--prefix', os.path.abspath(os.path.dirname(__file__)), 'build'], env=modified_env)

with open('package.json') as f:
    package = json.load(f)

package_name = package["name"].replace(" ", "_").replace("-", "_")

setup(
    name=package_name,
    version=package["version"],
    author=package['author'],
    packages=[package_name],
    include_package_data=True,
    license=package['license'],
    description=package.get('description', package_name),
    install_requires=[],
    classifiers=[
        'Framework :: Dash',
    ],
)
