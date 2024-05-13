'''
This file is designed to take an execution DAG (as a JSON object),
a set of parameters, and execute those queries.

The executor processes the `execution_dag` portion of our request.
'''
import asyncio
import collections
import concurrent.futures
import enum
import functools
import inspect

import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.util
import learning_observer.kvs
import learning_observer.module_loader
import learning_observer.settings
import learning_observer.stream_analytics.fields
import learning_observer.stream_analytics.helpers
from learning_observer.log_event import debug_log
from learning_observer.util import get_nested_dict_value, clean_json
from learning_observer.communication_protocol.exception import DAGExecutionException

dispatch = learning_observer.communication_protocol.query.dispatch


def unimplemented_handler(*args, **kwargs):
    """
    We use a handler for mapping different types of nodes to their appropriate
    functions in an execution DAG.
    This function is used as a default when the function for a given node is not found.
    """
    raise DAGExecutionException(
        'Unimplemented function',
        inspect.currentframe().f_code.co_name,
        {'args': args, 'kwargs': kwargs}
    )


DISPATCH = collections.defaultdict(lambda: unimplemented_handler)


def handler(name):
    """
    Add mapping for nodes of type `name` in an execution DAG
    to their appropriate server-side functions.
    Raises an exception when duplicate names are found
    """
    def decorator(f):
        if name in DISPATCH:
            raise DAGExecutionException(
                f'Duplicate entry for {name} found.',
                inspect.currentframe().f_code.co_name,
                {'handler': name, 'new_function': f, 'prior_function': DISPATCH[name]}
            )
        DISPATCH[name] = f
        return f
    return decorator


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.CALL)
async def call_dispatch(functions, function_name, args, kwargs):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.CALL node.
    This is used when users want to call functions on the server and use their
    output within an execution DAG. Some of these functions include:
    * `courseroster(request, course_id)`
    * `process_document_data(text)`

    We run the function, `function_name`, in `functions` with any `args` or
    `kwargs` and return the result.

    Generic double function for testing
    >>> def double(x):
    ...     if x is None:
    ...         raise ValueError("Input cannot be None")
    ...     return x * 2

    Simple call to double with args [1]
    >>> asyncio.run(call_dispatch({'double': double}, 'double', [1], {}))
    2

    Raises an exception when function `nonexistent` is not found.
    >>> asyncio.run(call_dispatch({'double': double}, 'nonexistent', [1], {}))
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Function nonexistent did not execute properly during call.', 'call_dispatch', {'function_name': 'nonexistent', 'args': [1], 'kwargs': {}, 'error': "'nonexistent'"}, ...)


    Raises an exception when the called function raises an exception.
    >>> asyncio.run(call_dispatch({'double': double}, 'double', [None], {}))
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Function double did not execute properly during call.', 'call_dispatch', {'function_name': 'double', 'args': [None], 'kwargs': {}, 'error': 'Input cannot be None'}, ...)
    """
    try:
        function = functions[function_name]
        result = function(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
    except Exception as e:
        raise DAGExecutionException(
            f'Function {function_name} did not execute properly during call.',
            inspect.currentframe().f_code.co_name,
            {'function_name': function_name, 'args': args, 'kwargs': kwargs, 'error': str(e)},
            e.__traceback__
        )
    return result


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER)
def substitute_parameter(parameter_name, parameters, required, default):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.PARAMETER node.
    This function is used to substitute parameters provided by the user into future
    nodes. When defining the node, a default may be provided.

    Standard scenario fetching a required parameter
    >>> substitute_parameter('param1key', {'param1key': 'param1val'}, True, None)
    'param1val'

    Standard scenario fetching a nonexistent optional parameter and using the default
    >>> substitute_parameter('param2key', {'param1key': 'param1val'}, False, 'defaultvalue')
    'defaultvalue'

    Raise an exception when a required parameter is missing
    >>> substitute_parameter('param2key', {'param1key': 'param1val'}, True, None)
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Required parameter `param2key` was not found in parameters.', 'substitute_parameter', {'parameter_name': 'param2key', 'parameters': {'param1key': 'param1val'}})
    """
    if parameter_name not in parameters:
        if required:
            raise DAGExecutionException(
                f'Required parameter `{parameter_name}` was not found in parameters.',
                inspect.currentframe().f_code.co_name,
                {'parameter_name': parameter_name, 'parameters': parameters}
            )
        else:
            return default
    return parameters[parameter_name]


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.JOIN)
def handle_join(left, right, left_on, right_on):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.JOIN node.
    Users will use this when they want to combine the output of multiple nodes.

    Both `left_on` and `right_on` support nested dot notation. That is,
    ```python
    some_dict = {'some': {'nested': {'key': 'value'}}}
    normal_access = some_dict['some']['nested']['key']
    dot_access = get_nested_dict_value(some_dict, 'some.nested.key')
    assert(normal_access == dot_access)
    ```

    Generic join where left.lid == right.rid
    >>> handle_join(
    ...     left=[{'lid': 1, 'left': True}, {'lid': 2, 'left': True}],
    ...     right=[{'rid': 2, 'right': True}, {'rid': 1, 'right': True}],
    ...     left_on='lid', right_on='rid'
    ... )
    [{'lid': 1, 'left': True, 'rid': 1, 'right': True}, {'lid': 2, 'left': True, 'rid': 2, 'right': True}]

    We return every item in `left` even if they do not have a matching item
    in `right`. This also demonstrates the behavior for `RIGHT_ON` not being found in
    one of the elements of `right`.
    >>> handle_join(
    ...     left=[{'lid': 1, 'left': True}, {'lid': 2, 'left': True}],
    ...     right=[{'right': True}, {'rid': 1, 'right': True}],
    ...     left_on='lid', right_on='rid'
    ... )
    [{'lid': 1, 'left': True, 'rid': 1, 'right': True}, {'lid': 2, 'left': True}]

    When `LEFT_ON` is not found, we return an error. Instead of throwing exceptions,
    we return errors like normal results and allow the DAG executor to handle package
    them and bubble them up. This allows to only error on a singular item and allow
    the others to continue running.
    >>> handle_join(
    ...     left=[{'left': True}, {'lid': 2, 'left': True}],
    ...     right=[{'rid': 2, 'right': True}, {'rid': 1, 'right': True}],
    ...     left_on='lid', right_on='rid'
    ... )
    [{'error': "KeyError: key `lid` not found in `dict_keys(['left'])`", 'function': 'handle_join', 'error_provenance': {'target': {'left': True}, 'key': 'lid', 'exception': KeyError("Key lid not found in {'left': True}")}, 'timestamp': ... 'traceback': ... {'lid': 2, 'left': True, 'rid': 2, 'right': True}]
    """
    right_dict = {}
    for d in right:
        try:
            nested_value = get_nested_dict_value(d, right_on)
            right_dict[nested_value] = d
        except KeyError as e:
            pass

    result = []
    for left_dict in left:
        try:
            lookup_key = get_nested_dict_value(left_dict, left_on)
            right_dict_match = right_dict.get(lookup_key)

            if right_dict_match:
                merged_dict = {**left_dict, **right_dict_match}
            else:
                # defaults to left_dict if not match isn't found
                merged_dict = left_dict
            result.append(merged_dict)
        except KeyError as e:
            result.append(left_dict)
            # result.append(DAGExecutionException(
            #     f'KeyError: key `{left_on}` not found in `{left_dict.keys()}`',
            #     inspect.currentframe().f_code.co_name,
            #     {'target': left_dict, 'key': left_on, 'exception': e}
            # ).to_dict())

    return result


def exception_wrapper(func):
    """
    When we map values across a function, we want to catch any errors that may occur.
    For asynchronous functions, we are able to use `asyncio.gather` which allows us to return
    exceptions as normal results. This wrapper mimics this behavior for synchronous functions
    and returns any exceptions as normal results. These exceptions are later caught by the
    DAG executor and handled appropriately. This allows the system to keep executing the DAG even
    if some values raise exceptions.
    """
    def exception_catcher(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e
    return exception_catcher


async def map_coroutine_serial(func, values, value_path):
    """
    We call map for coroutine functions operating in serial.
    See the `handle_map` function for more details regarding parameters.
    """
    return await asyncio.gather(*[func(get_nested_dict_value(v, value_path)) for v in values], return_exceptions=True)


async def map_coroutine_parallel(func, values, value_path):
    """
    We call map for coroutine functions operating in parallel.
    See the `handle_map` function for more details regarding parameters.
    """
    raise DAGExecutionException(
        'Asynchronous parallelization has not yet been implemented.',
        inspect.currentframe().f_code.co_name,
        {'function': func, 'values': values, 'value_path': value_path}
    )


def map_parallel(func, values, value_path):
    """
    We call map for synchronous functions operating in parallel.
    See the `handle_map` function for more details regarding parameters.
    """
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # TODO catch any errors from get_nested_dict_value()
        futures = [executor.submit(func, get_nested_dict_value(v, value_path)) for v in values]
    results = [future.result() for future in futures]
    return results


def map_serial(func, values, value_path):
    """
    We call map for synchronous functions operating in serial.
    See the `handle_map` function for more details regarding parameters.
    """
    outputs = []
    for v in values:
        try:
            output = func(get_nested_dict_value(v, value_path))
        except DAGExecutionException as e:
            output = e.to_dict()
        outputs.append(output)
    return outputs


def annotate_map_metadata(function, results, values, value_path, func_kwargs):
    """
    We annotate the list of raw results from mapping over a function with provenance
    about the values passed in and the function used. Additionally, we want to
    provide the proper metadata and output for any exceptions that took place
    during execution of the map.
    """
    output = []
    for res, item in zip(results, values):
        provenance = {
            'function': function,
            'func_kwargs': func_kwargs,
            'value': item,
            'value_path': value_path
        }
        if isinstance(res, dict):
            out = res
        elif isinstance(res, Exception):
            error_provenance = provenance.copy()
            error_provenance['error'] = str(res)
            out = DAGExecutionException(
                f'Function {function} did not execute properly during map.',
                inspect.currentframe().f_code.co_name,
                error_provenance,
                res.__traceback__
            ).to_dict()
        else:
            out = {'output': res}
        out['provenance'] = provenance
        output.append(out)
    return output


MAPS = {
    'map_parallel': map_parallel,
    'map_serial': map_serial,
    'map_coroutine_parallel': map_coroutine_parallel,
    'map_coroutine_serial': map_coroutine_serial
}


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.MAP)
async def handle_map(functions, function_name, values, value_path, func_kwargs=None, parallel=False):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.MAP node.
    Users can run a single function across a set of values.

    We fetch the function found under `function_name` in the `functions` dictionary and
    apply any `func_kwargs` to it before calling the map function. The function is ran
    over the value found at `value_path` under each value in `values`. The `value_path`
    parameter supports dot notation.

    Generic double function for testing
    >>> def double(x):
    ...     if not isinstance(x, int):
    ...         raise ValueError("Input must be an int")
    ...     return x * 2

    Generic example of mapping a double function over [0, 1].
    >>> asyncio.run(handle_map({'double': double}, 'double', [{'path': i} for i in range(2)], 'path'))
    [{'output': 0, 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 0}, 'value_path': 'path'}}, {'output': 2, 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 1}, 'value_path': 'path'}}]

    Exceptions in each function with in the map are returned with normal results
    and handled later by the DAG executor. In our text, we return both a normal result
    and the result of an exception being caught.
    >>> asyncio.run(handle_map({'double': double}, 'double', [{'path': i} for i in [1, 'fail']], 'path'))
    [{'output': 2, 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 1}, 'value_path': 'path'}}, {'error': 'Function double did not execute properly during map.', 'function': 'annotate_map_metadata', 'error_provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 'fail'}, 'value_path': 'path', 'error': 'Input must be an int'}, 'timestamp': ... 'traceback': ... 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 'fail'}, 'value_path': 'path'}}]

    Example of trying to call nonexistent function, `triple`
    >>> asyncio.run(handle_map({'double': double}, 'triple', [{'path': i} for i in range(2)], 'path'))
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Could not find function `triple` in available functions.', 'handle_map', {'function_name': 'triple', 'available_functions': dict_keys(['double']), 'error': "'triple'"}, ...)
    """
    if func_kwargs is None:
        func_kwargs = {}
    try:
        func = functions[function_name]
    except KeyError as e:
        raise DAGExecutionException(
            f'Could not find function `{function_name}` in available functions.',
            inspect.currentframe().f_code.co_name,
            {'function_name': function_name, 'available_functions': functions.keys(), 'error': str(e)},
            e.__traceback__
        )
    func_with_kwargs = functools.partial(func, **func_kwargs)
    is_coroutine = inspect.iscoroutinefunction(func)
    map_function = MAPS[f'map{"_coroutine" if is_coroutine else ""}_{"parallel" if parallel else "serial"}']
    if not is_coroutine:
        # wrap sync functions to return errors similar to asyncio.gather
        func_with_kwargs = exception_wrapper(func_with_kwargs)

    results = map_function(func_with_kwargs, values, value_path)
    if inspect.isawaitable(results):
        results = await results

    output = annotate_map_metadata(function_name, results, values, value_path, func_kwargs)
    return output


class SelectFields(enum.Enum):
    Missing = 'Missing'
    All = 'All'


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.SELECT)
async def handle_select(keys, fields=SelectFields.Missing):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.SELECT node.
    This function is used to select data from a kvs. The data being selected
    is usually the output or the default from a reducer.

    Currently, we only select data from the default learning_observer kvs.
    TODO pass kvs as a parameter

    This function expects a list of dicts that contain a 'key' attribute as well
    as which fields to include. The fields should be specified as a dictionary
    where the keys are the dot notation you are looking for and the values are
    the key they are returned under.

    TODO add in test cases once we pass kvs as a parameter
    """
    fields_to_keep = fields
    if fields is None or fields == SelectFields.Missing.value:
        fields_to_keep = {}

    response = []
    for k in keys:
        if isinstance(k, dict) and 'key' in k:
            # output from query added to response later
            query_response_element = {
                'provenance': {
                    'key': k['key'],
                    'provenance': k['provenance']
                }
            }
        else:
            raise DAGExecutionException(
                f'Key not formatted correctly for select: {k}',
                inspect.currentframe().f_code.co_name,
                {'keys': keys, 'fields': fields}
            )
        resulting_value = await learning_observer.kvs.KVS()[k['key']]
        if resulting_value is None:
            # the reducer has not run yet, so we return the default value from the module
            resulting_value = k['default']

        # keep all current fields except for provenance (already prepared)
        if fields == SelectFields.All.value:
            fields_to_keep = {k: k for k in resulting_value.keys() if k != 'provenance'}

        for f in fields_to_keep:
            try:
                value = get_nested_dict_value(resulting_value, f)
            except KeyError as e:
                value = DAGExecutionException(
                    f'KeyError: key `{f}` not found in `{resulting_value.keys()}`',
                    inspect.currentframe().f_code.co_name,
                    {'target': resulting_value, 'key': f, 'exception': e}
                ).to_dict()
            # add necessary outputs to query response
            query_response_element[fields_to_keep[f]] = value
        response.append(query_response_element)
    return response


# @handler(learning_observer.communication_protocol.query.DISPATCH_MODES.KEYS)
def handle_keys(function, value_path, **kwargs):
    """
    We WANT TO dispatch this function whenever we process a DISPATCH_MODES.KEYS node.
    Whenever a user wants to perform a select operation, they first must make sure their
    keys are formatted properly. This method builds the keys to access the appropriate
    reducers output.

    We have not yet implemented this because there is not a clear way of how different
    sets of KeyFields should interact with one another. The easy solution is when we
    just have a single KeyField. For example, with Students, we iterate over each one
    and create the key. It is not clear how each item in the superset of KeyField
    combinations should behave.

    Currently we use `hack_handle_keys` instead.
    """
    return unimplemented_handler()


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.KEYS)
def hack_handle_keys(function, STUDENTS=None, STUDENTS_path=None, RESOURCES=None, RESOURCES_path=None):
    """
    We INSTEAD dispatch this function whenever we process a DISPATCH_MODES.KEYS node.
    Whenever a user wants to perform a select operation, they first must make sure their
    keys are formatted properly. This method builds the keys to access the appropriate
    reducers output.

    This function only supports the creation of Student keys and Student/Resource pair keys.
    We create a list of fields needed for the `make_key()` function as well as the provenance
    associated with each. These are zipped together and returned to the user.
    """
    func = next((item for item in learning_observer.module_loader.reducers() if item['id'] == function), None)
    fields = []
    provenances = []
    if STUDENTS is not None and RESOURCES is None:
        # handle only students
        fields = [
            {
                learning_observer.stream_analytics.fields.KeyField.STUDENT: get_nested_dict_value(s, STUDENTS_path)  # TODO catch get_nested_dict_value errors
            } for s in STUDENTS
        ]
        provenances = [s.get('provenance', {'value': s}) for s in STUDENTS]
    elif STUDENTS is not None and RESOURCES is not None:
        # handle both students and resources
        fields = [
            {
                learning_observer.stream_analytics.fields.KeyField.STUDENT: get_nested_dict_value(s, STUDENTS_path),  # TODO catch get_nested_dict_value errors
                learning_observer.stream_analytics.helpers.EventField('doc_id'): get_nested_dict_value(r, RESOURCES_path, '')  # TODO catch get_nested_dict_value errors
            } for s, r in zip(STUDENTS, RESOURCES)
        ]
        provenances = [
            {
                'STUDENT': s.get('provenance', {'value': s}),
                'RESOURCE': r.get('provenance', {'value': r})
            } for s, r in zip(STUDENTS, RESOURCES)
        ]

    keys = []
    for f, p in zip(fields, provenances):
        key = learning_observer.stream_analytics.helpers.make_key(
            func['function'],
            f,
            learning_observer.stream_analytics.fields.KeyStateType.INTERNAL
        )
        keys.append(
            {
                'key': key,
                'provenance': p,
                'default': func['default']
            }
        )
    return keys


def _has_error(node):
    '''
    When executing a DAG, we may return an error. This function returns the first
    error found, so that it can be further bubbled up the execution tree.

    FIXME Possible bottleneck in this code. The following uses DFS when checking
    for errors. Since a DAG can split off and rejoin, we may get iterate over the
    same nodes multiple times. We have simple DAGs, so for now it should not be a
    problem. However, we ought to change this to a BFS or add a visited node tracker.
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


def _find_error_messages(d):
    '''
    We want to collect all the error messages that occured within the
    communication protocol and return them so they user can clearly
    see what went wrong.
    '''
    errors = []

    def collect_errors(item):
        '''Iterate over each item in the object and return any error
        messages we find
        '''
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'error' and type(value) == str:
                    errors.append(value)
                else:
                    collect_errors(value)
        elif isinstance(item, list):
            for element in item:
                collect_errors(element)

    collect_errors(d)
    return errors


def strip_provenance(variable):
    '''
    Context is included for debugging purposes, but should not be included
    in deployed settings. This function removes all instances of 'provenance'
    from a variable.

    Generic removal of `provenance` key from dict.
    >>> strip_provenance({'provenance': 123, 'other': 123})
    {'other': 123}

    Removal of `provenance` from list of dicts.
    >>> strip_provenance([{'provenance': 123, 'other': 123}, {'provenance': 123, 'other': 123}, {'provenance': 123, 'other': 123}])
    [{'other': 123}, {'other': 123}, {'other': 123}]

    If we don't have a dict, we do not change or remove anything.
    >>> strip_provenance(1)
    1
    >>> strip_provenance([1, 2, 3])
    [1, 2, 3]

    Each provenance item should appear at the top-level of a dictionary, so
    nested provenance key/value pairs are still included.
    >>> strip_provenance({'nested_dict': {'provenance': 123, 'other': 123}})
    {'nested_dict': {'provenance': 123, 'other': 123}}
    '''
    if isinstance(variable, dict):
        return {key: value for key, value in variable.items() if key != 'provenance'}
    elif isinstance(variable, list):
        return [strip_provenance(item) if isinstance(item, dict) else item for item in variable]
    else:
        return variable


async def execute_dag(endpoint, parameters, functions, target_exports):
    """
    This is the primary way to execute a DAG.
    Users should pass the overall execution dag dict, a dictionary parameters,
    a dictionary of available functions, and a list of exports they wish to
    receive data back for.

    See `learning_observer/communication_protocol/test_cases.py` for usage examples.
    """
    target_nodes = [endpoint['exports'][key]['returns'] for key in target_exports]

    visited = set()
    nodes = endpoint['execution_dag']

    async def dispatch_node(node):
        """
        Dispatch the appropriate server-side function for a given node.
        """
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
            if inspect.isawaitable(result):
                result = await result
            return result
        except DAGExecutionException as e:
            return e.to_dict()

    async def walk_dict(node_dict):
        """
        We walk through the execution DAG backwards. We visit any variable nodes
        we find and cache their stored value.
        """
        for child_key, child_value in list(node_dict.items()):
            if isinstance(child_value, dict) and dispatch in child_value and child_value[dispatch] == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
                node_dict[child_key] = await visit(child_value['variable_name'])
            elif isinstance(child_value, dict):
                await walk_dict(child_value)

    async def visit(node_name):
        """
        When executing the DAG, we `visit()` nodes that we want output from.
        These will either be specified as target_nodes or be any descendents
        of the target_nodes.

        If we've already visited a node, we return the result.
        If any of the child nodes return errors, we return them.
        """
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
            error_texts = '\n'.join((f'  {e}' for e in _find_error_messages(error)))
            tb = nodes[node_name]["error"].get("traceback", 'No traceback available')
            debug_log('ERROR:: Error occured within execution dag at '\
                      f'{node_name}\n{tb}\n'\
                      f'{error_texts}')
        else:
            nodes[node_name] = await dispatch_node(nodes[node_name])

        visited.add(node_name)
        return nodes[node_name]

    # Include execution history in output if operating in development settings
    if learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV:
        return {e: clean_json(await visit(e)) for e in target_nodes}

    # Remove execution history if in deployed settings, with data flowing back to teacher dashboards
    return {e: clean_json(strip_provenance(await visit(e))) for e in target_nodes}


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
