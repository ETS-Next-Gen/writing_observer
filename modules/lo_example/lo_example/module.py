'''
Module Example
'''
import learning_observer.downloads as d
import learning_observer.communication_protocol.query as q
from learning_observer.dash_integration import thirdparty_url, static_url
from learning_observer.stream_analytics.helpers import KeyField, Scope

import lo_example.reducers
import lo_example.dash_dashboard

# Name for the module
NAME = 'Learning Observer Example'

'''
Define execution DAGs for this module

`execution_dag`: defined directed acyclic graph (DAG) for querying data
    <node name>: q.select() # or some other communication protocol query
`exports`: fetchable nodes from the execution dag
    <name for export>: {
        "returns": <node name>,
        "parameters": ["list", "of", "parameters", "needed"]
    }

NOTE interfacing with the communication protocol may change,
the current flow is the first iteration. We will mark where things
ought to be improved.
'''
# q.call converts functions to callable nodes on the execution DAG.
# This one fetches roster information.
course_roster = q.call('learning_observer.courseroster')
EXECUTION_DAG = {
    'execution_dag': {
        # If we include runtime as a parameter, then the runtime object,
        # which contains the current request, will be passed to the function.
        # course_roster expects a `course_id` which we define as q.parameter.
        # `course_id` should be provided when querying a node that depends
        # on this function.
        'roster': course_roster(runtime=q.parameter('runtime'), course_id=q.parameter("course_id", required=True)),
        # q.keys formats requested information into the appropriate keys
        'student_keys': q.keys('lo_example.event_count', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'),
        # q.select handles fetching items from redis based on a list of keys
        'event_counts': q.select(q.variable('student_keys'), fields={'count': 'count'}),
        # q.join will combine two lists of dictionaries based on a key_path
        'events_join_roster': q.join(LEFT=q.variable("event_counts"), RIGHT=q.variable("roster"), LEFT_ON='provenance.provenance.value.user_id', RIGHT_ON='user_id'),
    },
    'exports': {
        'student_event_counts': {
            'returns': 'events_join_roster',
            # TODO we ought to automatically know the parameters based on
            # the queried node. Including a list of parameters here is
            # redundant.
            'parameters': ['course_id'],
            # TODO include a description for each exported node
            # TODO include sample output for the exported node
        }
    }
}

'''
Add reducers to the module.

`context`: TODO
`scope`: the granularity of event (by student, by student + document, etc)
`function`: the reducer function to run
`default` (optional): initial value to start with
'''
REDUCERS = [
    {
        'context': 'org.mitros.writing_analytics',
        # TODO scope is defined as a decorator on the function, why is
        # is also defined here?
        'scope': Scope([KeyField.STUDENT]),
        'function': lo_example.reducers.event_count,
        'default': {'count': 0}
    }
]

'''
Define pages created with Dash.
'''
DASH_PAGES = [
    {
        'MODULE': lo_example.dash_dashboard,
        'LAYOUT': lo_example.dash_dashboard.layout,
        'ASSETS': 'assets',
        'TITLE': 'Title of Page',
        'DESCRIPTION': 'Description of the page',
        'SUBPATH': 'lo-example',
        'CSS': [
            thirdparty_url("css/fontawesome_all.css")
        ],
        'SCRIPTS': [
            static_url("liblo.js")
        ]
    }
]

'''
Additional files we want included that come from a third part.
'''
THIRD_PARTY = {
    "css/fontawesome_all.css": d.FONTAWESOME_CSS,
    "webfonts/fa-solid-900.woff2": d.FONTAWESOME_WOFF2,
    "webfonts/fa-solid-900.ttf": d.FONTAWESOME_TTF
}

'''
The Course Dashboards are used to populate the modules
on the home screen.

Note the icon uses Font Awesome v5
'''
COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/lo_example/dash/lo-example",
    "icon": {
        "type": "fas",
        "icon": "fa-play-circle"
    }
}]
