'''
This file provides utility functions specific to the
communication protocol.
'''
import inspect

import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.exception
import learning_observer.util

dispatch = learning_observer.communication_protocol.query.dispatch


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
        if isinstance(value, dict) and dispatch in value and value[dispatch] != learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
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


def get_nested_dict_value(d, key_str=None):
    '''
    Wrapper for learning_observer.util.get_nested_dict_value that
    will raise a DAGExecutionException if the key_str is not found
    '''
    k = key_str
    output = learning_observer.util.get_nested_dict_value(d, k)
    # FIXME if the output is None, then we still raise an error
    # we ought to allow the output to be None without raising an error
    # sometimes the default of a reducer might be None
    if output is None:
        raise learning_observer.communication_protocol.exception.DAGExecutionException(
            f'Field `{key_str}` not found in {d}. '
            'Ensure the keys are present within d.',
            inspect.currentframe().f_code.co_name,
            {'dict': d, 'key_string': key_str}
        )
    return output
