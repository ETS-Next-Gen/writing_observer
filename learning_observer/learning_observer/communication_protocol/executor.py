'''
The executor processes the `execution_dag` portion of our request.
This also includes some utility functions.
'''
import collections
import copy
import inspect
import json

import learning_observer.communication_protocol.request
import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.kvs

dispatch = learning_observer.communication_protocol.request.dispatch
# TODO create connection to our kvs so we access the data
# kvs = learning_observer.kvs.KVS()


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


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.CALL)
async def call_dispatch(functions, function_name, args, kwargs):
    """
    Calls a function from the available functions.

    :param functions: Dictionary of available functions
    :type functions: dict
    :param function_name: The name of the function to be called
    :type function_name: str
    :param args: The positional arguments for the function
    :type args: list
    :param kwargs: The keyword arguments for the function
    :type kwargs: dict
    :return: The result of the function call
    """
    function = functions[function_name]
    result = function(*args, **kwargs)
    if inspect.iscoroutinefunction(function):
        result = await result
    return result


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.PARAMETER)
def substitute_parameter(parameter_name, parameters):
    """
    Substitutes a parameter from the provided parameters.

    :param parameter_name: The name of the parameter to be substituted
    :type parameter_name: str
    :param parameters: The dictionary of available parameters
    :type parameters: dict
    :return: The value of the parameter
    """
    return parameters[parameter_name]


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.JOIN)
def handle_join(left, right, left_on=None, right_on=None):
    """
    Joins two lists of dictionaries based on provided keys. If no keys are provided, zips the lists together.

    :param left: The left list of dictionaries
    :type left: list
    :param right: The right list of dictionaries
    :type right: list
    :param left_on: The key on which to join from the left list, defaults to None
    :type left_on: str, optional
    :param right_on: The key on which to join from the right list, defaults to None
    :type right_on: str, optional
    :return: The joined list
    :rtype: list
    """
    if not left_on or not right_on:
        return [(le, r) for le, r in zip(left, right)]
    return [dict(**le, **r) for le, r in zip(left, right) if le.get(left_on) == r.get(right_on)]


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.MAP)
async def map_function(functions, function, values):
    """
    Applies a function to a list of values.

    :param functions: Dictionary of available functions
    :type functions: dict
    :param function: The function to be applied
    :type function: str
    :param values: The values to be mapped
    :type values: list
    :return: The mapped values
    :rtype: list
    """
    func = functions[function]
    if inspect.iscoroutinefunction(func):
        return [await func(v) for v in values]
    return map(func, values)


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.SELECT)
def handle_select(keys):
    """
    Placeholder function to select data from a key-value store (KVS). Currently returns mock data.

    :param keys: The keys to select data for
    :type keys: list
    :return: The selected data
    :rtype: list
    """
    # TODO fix this to actually call the kvs, will need async overhaul first
    # data = await kvs.multiget(keys=keys)
    data = [f'fetched-{i}' for i in keys]
    return data


@handler(learning_observer.communication_protocol.request.DISPATCH_MODES.KEYS)
def handle_keys(function, items):
    """
    Placeholder function to generate keys for a function and list of items. Currently returns mock data.

    :param function: The function to generate keys for
    :type function: str
    :param items: The items to generate keys for
    :type items: list
    :return: The generated keys
    :rtype: list
    """
    # TODO Fix this code to properly implement
    # currently broken because funciton is only a string and
    # the method expects a callable
    #
    # keys = [sa_helpers.make_key(
    #     function,
    #     {},
    #     sa_helpers.KeyStateType.INTERNAL
    # ) for i in items]
    keys = [f'{function}-{i}' for i in items]
    return keys


async def execute_dag(endpoint, parameters, functions):
    """
    Execute a flattened directed acyclic graph (DAG).

    :param endpoint: The endpoint dictionary
    :type endpoint: dict
    :param parameters: The parameters for execution
    :type parameters: dict
    :param functions: The functions available for execution
    :type functions: dict
    :return: The result of the execution
    :rtype: list
    """
    visited = set()
    nodes = endpoint['execution_dag']

    async def dispatch_node(node):
        if not isinstance(node, dict):
            return node
        if dispatch not in node:
            return node
        node_dispatch = node[dispatch]
        function = DISPATCH[node_dispatch]
        del node[dispatch]
        # make dispatch specific function call
        if node_dispatch == learning_observer.communication_protocol.request.DISPATCH_MODES.PARAMETER:
            result = function(parameters=parameters, **node)
        elif (node_dispatch == learning_observer.communication_protocol.request.DISPATCH_MODES.CALL
              or node_dispatch == learning_observer.communication_protocol.request.DISPATCH_MODES.MAP):
            result = function(functions=functions, **node)
        else:
            result = function(**node)

        if inspect.iscoroutinefunction(function):
            result = await result
        return result

    async def walk_dict(node_dict):
        '''
        This will walk a dictionary, and call `visit` on all variables, and make the requisite substitions
        '''
        for child_key, child_value in list(node_dict.items()):
            if isinstance(child_value, dict) and dispatch in child_value and child_value[dispatch] == learning_observer.communication_protocol.request.DISPATCH_MODES.VARIABLE:
                node_dict[child_key] = await visit(child_value['variable_name'])
            elif isinstance(child_value, dict):
                await walk_dict(child_value)

    async def visit(node_name):
        # We've already done this one.
        if node_name in visited:
            return nodes[node_name]
        # Execute all the child nodes
        await walk_dict(nodes[node_name])
        # Execute the current node
        nodes[node_name] = await dispatch_node(nodes[node_name])
        visited.add(node_name)
        return nodes[node_name]

    return [await visit(e) for e in endpoint['returns']]


if __name__ == '__main__':
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

    print("Source:", json.dumps(learning_observer.communication_protocol.request.EXAMPLE, indent=2))
    FLAT = flatten(copy.deepcopy(learning_observer.communication_protocol.request.EXAMPLE))
    print("Flat:", json.dumps(FLAT, indent=2))
    import asyncio
    EXECUTE = asyncio.run(execute_dag(copy.deepcopy(FLAT), parameters={"course_id": 12345}, functions=functions))
    print("Execute:", json.dumps(EXECUTE, indent=2))
