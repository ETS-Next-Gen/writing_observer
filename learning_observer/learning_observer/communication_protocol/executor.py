'''
This file is designed to take an execution DAG (as a JSON object),
a set of parameters, and execute those queries.

The executor processes the `execution_dag` portion of our request.
This also includes some utility functions.

This should be broken up into pieces:

1. Generic utilities, like `flatten`
2. Test framework (instead of `if __name__ == '__main__'`)
3. Calls into the `learning_observer`, so we can eventually use this
   in other contexts (specifically, learning_observer.module_loader)
4. Core code for executing the JSON DAG
'''
import collections
import copy
import datetime
import inspect
import json
import traceback

import learning_observer.communication_protocol.query
import learning_observer.kvs
import learning_observer.module_loader
import learning_observer.settings
import learning_observer.stream_analytics.fields
import learning_observer.stream_analytics.helpers

dispatch = learning_observer.communication_protocol.query.dispatch

KVS = None


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


def get_nested_dict_value(d, key_str):
    """
    Fetch an item from a nested dictionary using `.` to indicate nested keys

    :param d: Dictionary to be searched
    :type d: dict
    :param key_str: Keys to iterate over
    :type key_str: str
    :return: Value of nested dictionary
    """
    keys = key_str.split('.')
    for key in keys:
        if d is not None and key in d:
            d = d[key]
        else:
            return None
    return d


def unimplemented_handler(*args, **kwargs):
    """
    Handler for unimplemented functions.

    :param args: Positional arguments
    :param kwargs: Keyword arguments
    :return: A dictionary indicating unimplemented status
    :rtype: dict
    """
    # TODO raise a 501 error here
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


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.CALL)
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


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER)
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


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.JOIN)
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
    right_dict = {get_nested_dict_value(d, right_on): d for d in right if get_nested_dict_value(d, right_on) is not None}

    result = []
    for left_dict in left:
        lookup_key = get_nested_dict_value(left_dict, left_on)
        right_dict_match = right_dict.get(lookup_key)

        if right_dict_match:
            merged_dict = {**left_dict, **right_dict_match}
            result.append(merged_dict)

    # example of raising an error
    # raise DAGExecutionException('Error', 'handle_join', {'left': left, 'right': right, 'left_on': left_on, 'right_on': right_on}, {})
    return result


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.MAP)
async def map_function(functions, function, values, value_path):
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
    # TODO this needs context added still, this method is currently unused
    func = functions[function]
    if inspect.iscoroutinefunction(func):
        return [await func(v) if value_path is None else get_nested_dict_value(v, value_path) for v in values]
    return [func(v) if value_path is None else get_nested_dict_value(v, value_path) for v in values]


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.SELECT)
async def handle_select(keys, fields):
    """
    Select data from a key-value store (KVS) based on a list of keys.

    :param keys: The keys to select data for
    :type keys: list
    :param fields: A mapping of key paths to keys (similar to SQL `AS`), ex) `{path.to.item: output}`
    :type fields: dict
    :return: The selected data ex) `[{output: value, context: {}}, ...]`
    :rtype: list
    """
    if fields is None:
        fields = {}

    response = []
    for k in keys:
        item = {
            'context': {
                'key': k['key'],
                'context': k['context']
            }
        }
        kvs_out = await KVS()[k['key']]
        for f in fields:
            value = get_nested_dict_value(kvs_out, f)
            item[fields[f]] = value
        response.append(item)
    return response


# @handler(learning_observer.communication_protocol.query.DISPATCH_MODES.KEYS)
def handle_keys(function, value_path, **kwargs):
    """
    Placeholder function to generate keys for a function and list of items. Currently returns mock data.

    :param function: The function to generate keys for
    :type function: str
    :param items: The items to generate keys for
    :type items: list
    :return: The generated keys
    :rtype: list
    """
    # TODO figure out how we are making the keys with the keyfields variable below
    # Currently we have "STUDENT", "CLASS", "RESOURCE"
    # When only 1 is populated, we just create a key for each item
    # when more >1 is populated, we need to combine them in some way
    #
    # filter kwargs for KeyFields
    keyfields = {k: kwargs.get(k, None) for k in learning_observer.stream_analytics.fields.KeyFields}

    # NOTE this should be removed when the keyfields stuff above gets figured out
    items = []
    for key in kwargs:
        if key in learning_observer.stream_analytics.fields.KeyFields:
            # we currently overwrite items if more than one KeyField is used
            items = [{learning_observer.stream_analytics.fields.KeyField[key]: get_nested_dict_value(i, value_path)} for i in kwargs[key]]

    # TODO fetch the function of the specified reducer for `make_key`
    func = next((item for item in learning_observer.module_loader.reducers() if item['id'] == function), None)
    keys = []
    for i in items:
        key = learning_observer.stream_analytics.helpers.make_key(
            func['function'],
            i,
            learning_observer.stream_analytics.fields.KeyStateType.EXTERNAL
        )
        keys.append(
            {
                'key': key,
                'context': {
                    'function': function,
                    'context': i.get('context', {})
                }
            }
        )
    return keys


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.KEYS)
def hack_handle_keys(function, STUDENTS=None, STUDENTS_path=None, RESOURCES=None, RESOURCES_path=None):
    func = next((item for item in learning_observer.module_loader.reducers() if item['id'] == function), None)
    fields = []
    contexts = []
    if STUDENTS is not None and RESOURCES is None:
        # handle only students
        fields = [
            {
                learning_observer.stream_analytics.fields.KeyField.STUDENT: get_nested_dict_value(s, STUDENTS_path)
            } for s in STUDENTS
        ]
        contexts = [s.get('context', {'value': s}) for s in STUDENTS]
    elif STUDENTS is not None and RESOURCES is not None:
        # handle both students and resources
        fields = [
            {
                learning_observer.stream_analytics.fields.KeyField.STUDENT: get_nested_dict_value(s, STUDENTS_path),
                learning_observer.stream_analytics.helpers.EventField('doc_id'): get_nested_dict_value(r, RESOURCES_path)
            } for s, r in zip(STUDENTS, RESOURCES)
        ]
        contexts = [
            {
                'STUDENT': s.get('context', {'value': s}),
                'RESOURCE': r.get('context', {'value': r})
            } for s, r in zip(STUDENTS, RESOURCES)
        ]

    keys = []
    for f, c in zip(fields, contexts):
        key = learning_observer.stream_analytics.helpers.make_key(
            func['function'],
            f,
            learning_observer.stream_analytics.fields.KeyStateType.EXTERNAL
        )
        keys.append(
            {
                'key': key,
                'context': c
            }
        )
    # raise DAGExecutionException('bruh', 200)
    return keys


class DAGExecutionException(Exception):
    '''
    Exception for errors raised during the execution of the dag

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, error, function, inputs, context):
        self.error = error
        self.function = function
        self.inputs = inputs
        self.context = context

    def to_dict(self):
        print(''.join(traceback.format_tb(self.__traceback__)))
        return {
            'error': self.error,
            'function': self.function,
            'inputs': self.inputs,
            'context': self.context,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'traceback': ''.join(traceback.format_tb(self.__traceback__))
        }


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
    :rtype: dict
    """
    visited = set()
    nodes = endpoint['execution_dag']

    global KVS
    if KVS is None:
        KVS = learning_observer.kvs.KVS

    async def dispatch_node(node):
        try:
            if not isinstance(node, dict):
                return node
            if dispatch not in node:
                return node
            node_dispatch = node[dispatch]
            function = DISPATCH[node_dispatch]
            del node[dispatch]
            # make dispatch specific function call
            if node_dispatch == learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER:
                result = function(parameters=parameters, **node)
            elif (node_dispatch == learning_observer.communication_protocol.query.DISPATCH_MODES.CALL
                  or node_dispatch == learning_observer.communication_protocol.query.DISPATCH_MODES.MAP):
                result = function(functions=functions, **node)
            else:
                result = function(**node)

            if inspect.iscoroutinefunction(function):
                result = await result
            return result
        except DAGExecutionException as e:
            return [e.to_dict()]

    async def walk_dict(node_dict):
        '''
        This will walk a dictionary, and call `visit` on all variables, and make the requisite substitions
        '''
        for child_key, child_value in list(node_dict.items()):
            if isinstance(child_value, dict) and dispatch in child_value and child_value[dispatch] == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
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
        # TODO check for any children that have an error object instead
        # return error object that states which node_name we errored on and that there
        # exists an issue with the children (parameters) for it
        if any([isinstance(nodes[node_name][c], dict) and 'error' in nodes[node_name][c] for c in nodes[node_name]]):
            print('erroring up', node_name)
            nodes[node_name] = [{'error': 'stupid'}]
        else:
            nodes[node_name] = await dispatch_node(nodes[node_name])
        visited.add(node_name)
        # print('*****', node_name, json.dumps(nodes[node_name], indent=2, default=str))  # useful but produces a lot
        return nodes[node_name]

    if learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV:
        # return everything in dev mode
        return {e: await visit(e) for e in endpoint['returns']}
    # remove context from outputs
    # this breaks if `await visit(e)` does not return a list of dicts
    return {e: [{k: v for k, v in o.items() if k != 'context'} for o in await visit(e)] for e in endpoint['returns']}


FUNCTIONS = {}


def callable_function(name):
    """
    Decorator to record callable functions.

    :param name: The name of the handler
    :type name: str
    :return: Decorator function
    """
    def decorator(f):
        # TODO check for duplicates?
        FUNCTIONS[name] = f
        return f
    return decorator


def add_queries_to_module(named_queries, module):
    '''
    Add queries to each module as a callable object
    example: `writing_observer.docs_with_roster(course_id=course_id)`
    '''
    for query_name in named_queries:
        async def query_func(**kwargs):  # create new function
            flat = flatten(copy.deepcopy(named_queries[query_name]))
            output = await execute_dag(flat, parameters=kwargs, functions=FUNCTIONS)
            return output
        if hasattr(module, query_name):
            raise AttributeError(f'Attibute, {query_name}, already exists under {module.__name__}')
        else:
            setattr(module, query_name, query_func)


@callable_function('learning_observer.course_roster')
def dummy_roster(course):
    return [
        {
            'student': f'student-{i}'
        } for i in range(10)
    ]


def create_function(query):
    async def query_func(**kwargs):
        flat = flatten(copy.deepcopy(query))
        output = await execute_dag(flat, parameters=kwargs, functions=FUNCTIONS)
        return output
    return query_func


if __name__ == '__main__':
    def dummy_roster(course):
        """
        Dummy function for course roster.

        :param course: The course identifier
        :type course: str
        :return: A list of student identifiers
        :rtype: list
        """
        return [
            {
                'user_id': f'student-{i}'
            } for i in range(10)
        ]

    # Setup KVS since LO.KVS() isn't available here
    import collections

    def create_kvs():
        async def return_value():
            return {'some_key': {'nested': 'some_key_value'}}
        return collections.defaultdict(return_value)
    KVS = create_kvs

    functions = {
        "learning_observer.course_roster": dummy_roster
    }

    # print("Source:", json.dumps(learning_observer.communication_protocol.query.EXAMPLE, indent=2))
    FLAT = flatten(copy.deepcopy(learning_observer.communication_protocol.query.EXAMPLE))
    # print("Flat:", json.dumps(FLAT, indent=2))
    import asyncio
    EXECUTE = asyncio.run(execute_dag(copy.deepcopy(FLAT), parameters={"course_id": 12345}, functions=functions))
    print("Execute:", json.dumps(EXECUTE, indent=2))
