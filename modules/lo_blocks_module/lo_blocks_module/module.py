'''
LO Blocks module

A Learning Observer module for handling LO Block items.
'''
import learning_observer.communication_protocol.query as q
from learning_observer.communication_protocol.integration import publish_function
import learning_observer.communication_protocol.util
from learning_observer.stream_analytics.helpers import KeyField, Scope

import lo_blocks_module.reducers

# Name for the module
NAME = 'LO Blocks module'

COURSE_ROSTER = q.call('learning_observer.courseroster')
roster_echo_call = q.call('examples.roster_echo')

@publish_function('examples.roster_echo')
def roster_echo(user_id):
    return {'user_id': user_id, 'status': 'ok'}


EXECUTION_DAG = {
    "execution_dag": {
        "roster": COURSE_ROSTER(runtime=q.parameter("runtime"), course_id=q.parameter("course_id", required=True)),
        "page_last_visited": q.select(
            q.keys(
                "lo_blocks_module.page_last_visited",
                scope_fields={
                    'student': {'values': q.variable('roster'), 'path': 'user_id'},
                }
            ),
            fields={'last_visited': 'page'},
        ),
        "event_type_counter": q.select(
            q.keys(
                "lo_blocks_module.event_type_counter",
                scope_fields={
                    'student': {'values': q.variable('roster'), 'path': 'user_id'},
                    'page': {'values': q.variable('page_last_visited'), 'path': 'page'},
                }
            ),
            fields=q.SelectFields.All,
        ),
        "time_on_task": q.select(
            q.keys(
                "lo_blocks_module.time_on_task",
                scope_fields={
                    'student': {'values': q.variable('roster'), 'path': 'user_id'},
                    'page': {'values': q.variable('page_last_visited'), 'path': 'page'},
                }
            ),
            fields=q.SelectFields.All,
        ),
        "binned_time_on_task": q.select(
            q.keys(
                "lo_blocks_module.binned_time_on_task",
                scope_fields={
                    'student': {'values': q.variable('roster'), 'path': 'user_id'},
                    'page': {'values': q.variable('page_last_visited'), 'path': 'page'},
                }
            ),
            fields=q.SelectFields.All,
        ),
        "event_timeline": q.select(
            q.keys(
                "lo_blocks_module.event_timeline",
                scope_fields={
                    'student': {'values': q.variable('roster'), 'path': 'user_id'},
                    'page': {'values': q.variable('page_last_visited'), 'path': 'page'},
                }
            ),
            fields=q.SelectFields.All,
        ),
        'roster_map': q.map(
            roster_echo_call,
            values=q.variable('roster'),
            value_path='user_id',
        ),
    },
    "exports": {
        "page_last_visited": {
            "returns": "page_last_visited",
            "parameters": ["course_id"],
        },
        "event_type_counter": {
            "returns": "event_type_counter",
            "parameters": ["course_id"],
        },
        "time_on_task": {
            "returns": "time_on_task",
            "parameters": ["course_id"],
        },
        "binned_time_on_task": {
            "returns": "binned_time_on_task",
            "parameters": ["course_id"],
        },
        "event_timeline": {
            "returns": "event_timeline",
            "parameters": ["course_id"],
        },
        'roster_map': {
            'returns': 'roster_map',
            'parameters': ['course_id'],
        },
    },
}

'''
Add reducers to the module.
'''
REDUCERS = [
    {
        'context': 'org.ets.sba',
        'scope': Scope([KeyField.STUDENT]),
        'function': lo_blocks_module.reducers.page_last_visited,
    },
    {
        'context': 'org.ets.sba',
        'scope': lo_blocks_module.reducers.page_scope,
        'function': lo_blocks_module.reducers.event_type_counter,
    },
    {
        'context': "org.ets.sba",
        'scope': lo_blocks_module.reducers.page_scope,
        'function': lo_blocks_module.reducers.time_on_task,
        'default': {'saved_ts': 0}
    },
    {
        'context': "org.ets.sba",
        'scope': lo_blocks_module.reducers.page_scope,
        'function': lo_blocks_module.reducers.binned_time_on_task
    },
    {
        'context': "org.ets.sba",
        'scope': lo_blocks_module.reducers.page_scope,
        'function': lo_blocks_module.reducers.event_timeline
    },
]


'''
The Course Dashboards are used to populate the modules
on the home screen.

Note the icon uses Font Awesome v5
'''
COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/lo_blocks_module/dashboard/",
    "icon": {
        "type": "fas",
        "icon": "fa-play-circle"
    }
}]

'''
Next js dashboards
'''
NEXTJS_PAGES = [
    # {'path': 'dashboard/'},
]
