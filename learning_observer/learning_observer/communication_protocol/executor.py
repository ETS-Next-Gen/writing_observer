'''
This file is designed to take an execution DAG (as a JSON object),
a set of parameters, and execute those queries.

The executor processes the `execution_dag` portion of our request.
'''
import asyncio
import collections
import concurrent.futures
import datetime
import functools
import inspect
import traceback

import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.util
import learning_observer.kvs
import learning_observer.module_loader
import learning_observer.settings
import learning_observer.stream_analytics.fields
import learning_observer.stream_analytics.helpers
from learning_observer.util import get_nested_dict_value

dispatch = learning_observer.communication_protocol.query.dispatch

KVS = None


def unimplemented_handler(*args, **kwargs):
    """
    Handler for unimplemented functions.

    :param args: Positional arguments
    :param kwargs: Keyword arguments
    :return: A dictionary indicating unimplemented status
    :rtype: dict
    """
    raise DAGExecutionException(
        f'Unimplemented function',
        inspect.currentframe().f_code.co_name,
        {'args': args, 'kwargs': kwargs}
    )


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
    try:
        result = function(*args, **kwargs)
        if inspect.iscoroutinefunction(function):
            result = await result
    except Exception as e:
        raise DAGExecutionException(
            f'Function {function_name} did not execute properly during call.',
            inspect.currentframe().f_code.co_name,
            {'function_name': function_name, 'args': args, 'kwargs': kwargs, 'error': str(e)}
        )
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
    if parameter_name not in parameters:
        raise DAGExecutionException(
            f'Required parameter `{parameter_name}` was not found in parameters.',
            inspect.currentframe().f_code.co_name,
            {'parameter_name': parameter_name, 'parameters': parameters}
        )
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
    # TODO raise exceptions when needed
    right_dict = {get_nested_dict_value(d, right_on): d for d in right if get_nested_dict_value(d, right_on) is not None}

    result = []
    for left_dict in left:
        lookup_key = get_nested_dict_value(left_dict, left_on)
        right_dict_match = right_dict.get(lookup_key)

        if right_dict_match:
            merged_dict = {**left_dict, **right_dict_match}
            result.append(merged_dict)

    return result


def exception_wrapper(func):
    def exception_catcher(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e
    return exception_catcher


async def map_coroutine(func, values, value_path):
    return await asyncio.gather(*[func(get_nested_dict_value(v, value_path)) for v in values], return_exceptions=True)


def map_parallelize(func, values, value_path):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(func, get_nested_dict_value(v, value_path)) for v in values]
    results = [future.result() for future in futures]
    return results


def map_serialize(func, values, value_path):
    return [func(get_nested_dict_value(v, value_path)) for v in values]


def annotate_metadata(function, results, values, value_path, func_kwargs):
    output = []
    for res, item in zip(results, values):
        context = {
            'function': function,
            'func_kwargs': func_kwargs,
            'value': item,
            'value_path': value_path
        }
        if isinstance(res, dict):
            out = res
        elif isinstance(res, Exception):
            error_context = context.copy()
            error_context['error'] = str(res)
            out = DAGExecutionException(
                f'Function {function} did not execute properly during map.',
                inspect.currentframe().f_code.co_name,
                error_context
            ).to_dict()
        else:
            out = {'output': res}
        out['context'] = context
        output.append(out)
    return output


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.MAP)
async def handle_map(functions, function, values, value_path, func_kwargs=None, parallelize=False):
    """
    Applies a function to a list of values.

    :param functions: Dictionary of available functions
    :type functions: dict
    :param function: The function to be applied
    :type function: str
    :param values: The values objects that need to be mapped
    :type values: list
    :param value_path: The path to fetch the value to be mapped
    :type value_path: str
    :param func_kwargs: kwargs to include in function
    :type func_kwargs: dict
    :param parallelize: Run **synchronous** functions in parallel
    :type parallelize: bool
    :return: The mapped values
    :rtype: list
    """
    if func_kwargs is None:
        func_kwargs = {}
    func = functions[function]
    partial = functools.partial(func, **func_kwargs)
    if inspect.iscoroutinefunction(func):
        results = await map_coroutine(partial, values, value_path)
    else:
        exception_catcher = exception_wrapper(partial)
        if parallelize:
            results = map_parallelize(exception_catcher, values, value_path)
        else:
            results = map_serialize(exception_catcher, values, value_path)
    output = annotate_metadata(function, results, values, value_path, func_kwargs)
    return output


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
        if isinstance(k, dict) and 'key' in k:
            item = {
                'context': {
                    'key': k['key'],
                    'context': k['context']
                }
            }
        else:
            raise DAGExecutionException(
                f'Key not formatted correctly for select: {k}',
                inspect.currentframe().f_code.co_name,
                {'keys': keys, 'fields': fields}
            )
        kvs_out = await KVS[k['key']]
        if kvs_out is None:
            kvs_out = k['default']
        for f in fields:
            value = get_nested_dict_value(kvs_out, f)
            if value is None:
                raise DAGExecutionException(
                    f'Field `{f}` not found under {k["key"]}. '
                    'Ensure the keys in the fields parameter are available in the KVS output. '
                    'You can provide a default within the list of reducers.',
                    inspect.currentframe().f_code.co_name,
                    {'fields': fields, 'key': k['key'], 'kvs_out': kvs_out}
                )
            item[fields[f]] = value
        response.append(item)
    return response


# @handler(learning_observer.communication_protocol.query.DISPATCH_MODES.KEYS)
def handle_keys(function, value_path, **kwargs):
    """
    Currently unused handle keys function, we just use hack_keys

    :param function: The function to generate keys for
    :type function: str
    :param items: The items to generate keys for
    :type items: list
    :return: The generated keys
    :rtype: list
    """
    pass


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
                'context': c,
                'default': func['default']
            }
        )
    return keys


class DAGExecutionException(Exception):
    '''
    Exception for errors raised during the execution of the dag

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, error, function, context):
        self.error = error
        self.function = function
        self.context = context

    def to_dict(self):
        # TODO create serialize/deserialize methods for traceback
        return {
            'error': self.error,
            'function': self.function,
            'error_context': self.context,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'traceback': ''.join(traceback.format_tb(self.__traceback__))
        }


def _has_error(node):
    '''
    Non-recursive function to find and return 'error' value and its path from any dictionary within the node.
    '''
    queue = [(node, [])]  # start with the node and an empty path
    while queue:
        current, path = queue.pop(0)
        if 'error' in current:
            return current, path
        for c in current:
            if isinstance(current[c], dict):
                queue.append((current[c], path + [c]))
            elif isinstance(current[c], list):
                for idx, i in enumerate(current[c]):
                    if isinstance(i, dict):
                        queue.append((i, path + [c, idx]))
    return None, []


KEYS_TO_REMOVE = ['context']


def _sanitaize_output(variable):
    if isinstance(variable, dict):
        return {key: value for key, value in variable.items() if key not in KEYS_TO_REMOVE}
    elif isinstance(variable, list):
        return [_sanitaize_output(item) if isinstance(item, dict) else item for item in variable]
    else:
        return variable


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

    # sets default for any missing optional parameters
    for parameter in endpoint['parameters']:
        if parameter['id'] not in parameters and not parameter['required']:
            parameters[parameter['id']] = parameter['default']

    global KVS
    if KVS is None:
        KVS = learning_observer.kvs.KVS()

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
            return e.to_dict()

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

        # Check for any errors, then dispatch the node
        # if errors are present, we bubble them up the DAG
        error, error_path = _has_error(nodes[node_name])
        if error is not None:
            nodes[node_name] = {
                'error': error,
                'dispatch': nodes[node_name]['dispatch'],
                'error_path': error_path
            }
        else:
            nodes[node_name] = await dispatch_node(nodes[node_name])

        # import json
        # print('*****', node_name, json.dumps(nodes[node_name], indent=2, default=str))  # useful but produces a lot
        visited.add(node_name)
        return nodes[node_name]

    # return everything in dev mode
    if learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV:
        return {e: await visit(e) for e in endpoint['returns']}

    # otherwise remove context from outputs
    return {e: _sanitaize_output(await visit(e)) for e in endpoint['returns']}
