#!/usr/bin/python3
'''
Add user to a password file.
We shouldn't be reinventing wheels. But we couldn't find a good one.
'''

import argparse
import bcrypt
import datetime
import getpass
import os.path
import sys
import yaml


parser = argparse.ArgumentParser(
    description=__doc__.strip(),
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '--username'
)
parser.add_argument(
    '--password'
)
parser.add_argument(
    '--filename', required=True
)
parser.add_argument(
    '--notes'
)

args = parser.parse_args()

if args.username is None:
    username = input('Username: ')
else:
    username = args.username

if args.password is None:
    password = getpass.getpass('Password: ')
else:
    password = args.password

if os.path.exists(args.filename):
    data = yaml.safe_load(open(args.filename))
else:
    data = {}

if data is None:
    data = {}

if 'users' not in data:
    data['users'] = {}

if username not in data['users']:
    data['users'][username] = {}

if args.notes is not None:
    data['users'][username]['notes'] = args.notes

data['users'][username]['password'] = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt(12)
)

if 'created' not in data['users'][username]:
    data['users'][username]['created'] = datetime.datetime.utcnow()

data['users'][username]['updated'] = datetime.datetime.utcnow()

with open(args.filename, "w") as fp:
    yaml.dump(data, fp)
