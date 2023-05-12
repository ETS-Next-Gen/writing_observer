'''
The executor processes the `execution_dag` portion of our request.
This also includes some utility functions.
'''
import collections
import copy
import json

import learning_observer.communication_protocol.request

dispatch = learning_observer.communication_protocol.request.dispatch


def dummy_roster(course):
    """
    Dummy function for course roster.

    :param course: The course identifier
    :type course: str
    :return: A list of student identifiers
    :rtype: list
    """
    return list(range(10))


def dummy_latest_doc(student_id):
    """
    Dummy function for latest document.

    :param student_id: The student identifier
    :type student_id: str
    :return: A string representing the latest document
    :rtype: str
    """
    return f"abcd_{student_id}_docid"


functions = {
    "writing_observer.latest_doc": dummy_latest_doc,
    "learning_observer.course_roster": dummy_roster
}


# NOTE perhaps if flatten doesn't fit in the request or the executor module
# we may want to make a utilities module
def flatten_helper(top_level, current_level, prefix=''):
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
    result = {}
    for key, value in list(current_level.items()):
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and dispatch in value and value[dispatch] != learning_observer.communication_protocol.request.DISPATCH_MODES.VARIABLE:
            if isinstance(value, dict):
                top_level[new_key] = flatten_helper(top_level, value, prefix=new_key)
            else:
                top_level[new_key] = value
            current_level[key] = {
                dispatch: learning_observer.communication_protocol.request.DISPATCH_MODES.VARIABLE,
                "variable_name": new_key
            }
        elif isinstance(value, dict) and dispatch not in value:
            current_level[key] = flatten_helper(top_level, value, prefix=new_key)
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
        endpoint['execution_dag'][key] = flatten_helper(endpoint['execution_dag'], value, prefix=f"impl.{key}")

    return endpoint


def unimplemented_handler(*args, **kwargs):
    """
    Handler for unimplemented functions.

    :param args: Positional arguments
    :param kwargs: Keyword arguments
    :return: A dictionary indicating unimplemented status
    :rtype: dict
    """
    return {
        'issue': "UNIMPLEMENTED",
        'args': args,
        'kwargs': kwargs
    }


DISPATCH = collections.defaultdict(lambda: unimplemented_handler)


def handler(name):
    """
    Decorator for handlers.

    :param name: The name of the handler
    :type name: str
    :return: Decorator function
    """
    def decorator(f):
        DISPATCH[name] = f
        return f
    return decorator


# TODO do all of these need parameters? I'm still trying to fully understand the system - brad
# TODO give each of this a docstring, waiting until implemented
@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.CALL)
def call_dispatch(function_name, args, kwargs, parameters):
    function = functions[function_name]
    return function(*args, **kwargs)


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.PARAMETER)
def substitute_parameter(parameter_name, parameters):
    return parameters[parameter_name]


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.JOIN)
def handle_join(left, right, left_key, right_key, parameters):
    # TODO implement this
    return f'{left} {right} {left_key}, {right_key}'


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.VARIABLE)
def substitute_variable(variable_name, parameters):
    # TODO implement this
    return f'variable_name: {variable_name}'


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.MAP)
def map_function(function, values, parameters):
    # TODO implement this
    return f'mapping {function} {values}'


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.SELECT)
def handle_select(keys, parameters):
    # TODO implement this
    return f'selecting {keys}'


def execute_dag(endpoint, parameters):
    """
    Execute the directed acyclic graph (DAG).

    :param endpoint: The endpoint dictionary
    :type endpoint: dict
    :param parameters: The parameters for execution
    :type parameters: dict
    :return: The result of the execution
    :rtype: list
    """
    visited = set()
    nodes = endpoint['execution_dag']

    def dispatch_node(node):
        if not isinstance(node, dict):
            return node
        if dispatch not in node:
            return node
        function = DISPATCH[node[dispatch]]
        del node[dispatch]
        return function(parameters=parameters, **node)

    def walk_dict(node_dict):
        '''
        This will walk a dictionary, and call `visit` on all variables, and make the requisite substitions
        '''
        for child_key, child_value in list(node_dict.items()):
            if isinstance(child_value, dict) and dispatch in child_value and child_value[dispatch] == learning_observer.communication_protocol.request.DISPATCH_MODES.VARIABLE:
                node_dict[child_key] = visit(child_value['variable_name'])
            elif isinstance(child_value, dict):
                walk_dict(child_value)

    def visit(node_name):
        # We've already done this one.
        if node_name in visited:
            return nodes[node_name]
        # Execute all the child nodes
        walk_dict(nodes[node_name])
        # Execute the current node
        nodes[node_name] = dispatch_node(nodes[node_name])
        visited.add(node_name)
        return nodes[node_name]

    return list(map(visit, endpoint['returns']))


if __name__ == '__main__':
    import enum

    class MyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, enum.Enum):
                return obj.value
            return super().default(obj)

    print("Source:", json.dumps(learning_observer.communication_protocol.request.EXAMPLE, indent=2, cls=MyEncoder))
    FLAT = flatten(copy.deepcopy(learning_observer.communication_protocol.request.EXAMPLE))
    print("Flat:", json.dumps(FLAT, indent=2, cls=MyEncoder))
    EXECUTE = execute_dag(copy.deepcopy(FLAT), parameters={"course_id": 12345})
    # print(">>>", EXECUTE)
    print("Execute:", json.dumps(EXECUTE, indent=2, cls=MyEncoder))
