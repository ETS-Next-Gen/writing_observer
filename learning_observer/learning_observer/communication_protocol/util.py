'''
This file provides utility functions specific to the
communication protocol.
'''
import inspect

import learning_observer.communication_protocol.query as q
import learning_observer.communication_protocol.exception
import learning_observer.util

dispatch = q.dispatch


def _flatten_helper(top_level, current_level, prefix=''):
    """
    Flatten the dictionary.

    :param top_level: The top level dictionary
    :type top_level: dict
    :param current_level: The current level dictionary
    :type current_level: dict
    :param prefix: The prefix for new keys
    :type prefix: str
    :return: A flattened dictionary
    :rtype: dict
    """
    for key, value in list(current_level.items()):
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and dispatch in value and value[dispatch] != q.DISPATCH_MODES.VARIABLE:
            if isinstance(value, dict):
                top_level[new_key] = _flatten_helper(top_level, value, prefix=new_key)
            else:
                top_level[new_key] = value
            current_level[key] = {
                dispatch: learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE,
                "variable_name": new_key
            }
        elif isinstance(value, dict) and dispatch not in value:
            current_level[key] = _flatten_helper(top_level, value, prefix=new_key)
    return current_level


def flatten(endpoint):
    """
    Flatten the endpoint.

    :param endpoint: The endpoint dictionary
    :type endpoint: dict
    :return: A flattened endpoint
    :rtype: dict
    """
    for key, value in list(endpoint['execution_dag'].items()):
        endpoint['execution_dag'][key] = _flatten_helper(endpoint['execution_dag'], value, prefix=f"impl.{key}")

    return endpoint


def generate_base_dag_for_student_reducer(reducer, module):
    course_roster = q.call('learning_observer.courseroster')
    keys_node = f'{reducer}_keys'
    select_node = f'{reducer}_output'
    join_node = f'{reducer}_join_roster'
    export_name = f'{reducer}_export'
    execution_dag = {
        'execution_dag': {
            # If we include runtime as a parameter, then the runtime object,
            # which contains the current request, will be passed to the function.
            # course_roster expects a `course_id` which we define as q.parameter.
            # `course_id` should be provided when querying a node that depends
            # on this function.
            'roster': course_roster(runtime=q.parameter('runtime'), course_id=q.parameter("course_id", required=True)),
            # q.keys formats requested information into the appropriate keys
            keys_node: q.keys(f'{module}.{reducer}', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'),
            # q.select handles fetching items from redis based on a list of keys
            select_node: q.select(q.variable(keys_node), fields=q.SelectFields.All),
            # q.join will combine two lists of dictionaries based on a key_path
            join_node: q.join(LEFT=q.variable(select_node), RIGHT=q.variable('roster'), LEFT_ON='provenance.provenance.value.user_id', RIGHT_ON='user_id'),
        },
        'exports': {
            export_name: {
                'returns': join_node,
                # TODO we ought to automatically know the parameters based on
                # the queried node. Including a list of parameters here is
                # redundant.
                'parameters': ['course_id'],
                # TODO include a description for each exported node
                # TODO include sample output for the exported node
            }
        }
    }
    return execution_dag
