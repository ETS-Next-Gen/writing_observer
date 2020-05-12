''' Abstraction to access database '''
import asyncio
import functools

import json
import yaml

import asyncpg

sql_statements = yaml.safe_load(open("init.sql"))

conn = None

stored_procedures = {}

async def initialize(reset=False):
    pass

async def set_resource_state(username, resource):
    pass

async def get_resource_state(username, resource):
    pass

async def fetch_events(username, resource):
    '''
    Grab all the events for a particular user / resource

    `resource` is typically `googledocs://docstring`
    '''
    pass

async def insert_event (username, resource, event):
    '''
    Store an event in the database 
    '''
    pass

async def get_class(username, class=None):
    '''
    Return all the students in a teacher's class.

    Teachers can have multiple classes.
    '''
    pass

async def get_recipients(username):
    '''
    Return all the teachers who should be notified of events for user
    `username`
    '''
