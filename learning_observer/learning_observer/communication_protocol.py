'''
This file defines the base schema for the client/server
communication protocol.

When a new message is received from the client, we validate
it against the module specific schema (or the base schema when
one is not found for a given module) using jsonschema
'''

base_schema = {
    'type': 'object',
    'properties': {
        'user_id': {'type': 'string'},
        'timestamp': {'type': 'string', 'format': 'date-time'}
    },
    'required': ['user_id', 'timestamp'],
}

websocket_receive = {
    'type': 'object',
    'properties': {
        'course_id': {'type': 'string'},
        'module': {'type': ['string', 'object']},
        'parameters': {'type': 'object'},
        'timestamp': {'type': 'string', 'format': 'date-time'}
    },
    'required': ['course_id', 'module', 'parameters'],
}
