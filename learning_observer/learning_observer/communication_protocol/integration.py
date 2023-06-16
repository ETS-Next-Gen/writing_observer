'''
This file handles integrating queries into the
Learning Observer platform.
'''
import copy

import learning_observer.communication_protocol.executor
import learning_observer.communication_protocol.util

FUNCTIONS = {}
DUPLICATE_FUNCTION_FOUND = """Duplicate function name found: {name}.
Please ensure that all callable functions used in the
communication protocol have different names.
Search the codebase for `publish_function({name})` to view
any duplicates.
"""


def publish_function(name):
    """
    Decorator to expose functions to the communication protocol.

    Args:
        name: The name of the handler.

    Returns:
        The decorator function.

    Example Usage:
        @publish_function("my_function")
        def my_function_handler():
            pass

    Note:
        This decorator adds the decorated function to the `FUNCTIONS` dictionary
        with the specified name as the key. The function can later be executed
        as part of a DAG call using the `create_function` function.
    """
    def decorator(f):
        if name in FUNCTIONS:
            # NOTE perhaps we should include some form of priority
            # use case: we may want to overwrite the roster function for a specific system
            raise KeyError(DUPLICATE_FUNCTION_FOUND.format(name=name))
        FUNCTIONS[name] = f
        return f
    return decorator


def add_queries_to_module(named_queries, module):
    '''
    Add queries to each module as a callable object.

    The `set_query_with_name` inner closure is necessary to appropriately
    set the `name` parameter within the `query_func` inner-most function.

    Args:
        named_queries: A dictionary containing named queries.
        module: The module to which the queries will be added.

    Example Usage:
        queries = {
            "query1": ...,
            "query2": ...,
        }
        add_queries_to_module(queries, my_module)
        result = await my_module.query1(parameter1=123)

    Raises:
        AttributeError: If the attribute name already exists in the module.

    Note:
        This function iterates over the named queries and adds each query as a
        callable object to the specified module. The queries can be executed
        by calling them as attributes of the module.
    '''
    for query_name in named_queries:
        def set_query_with_name(name):
            async def query_func(**kwargs):  # create new function
                flat = learning_observer.communication_protocol.util.flatten(copy.deepcopy(named_queries[name]))
                output = await learning_observer.communication_protocol.executor.execute_dag(flat, parameters=kwargs, functions=FUNCTIONS)
                return output
            if hasattr(module, name):
                raise AttributeError(f'Attibute, {name}, already exists under {module}')
            else:
                setattr(module, name, query_func)
        set_query_with_name(query_name)


def create_function(query):
    '''
    Creates a query function for executing a DAG (Directed Acyclic Graph) based on the provided query.

    Args:
        query: A query object representing the DAG to be executed.

    Returns:
        A query function that can be used to execute the DAG.

    Example Usage:
        query_obj = ...  # create the query object
        query_function = create_function(query_obj)
        result = await query_function(param1=value1, param2=value2)

    Note:
        The query object is flattened and passed to an executor to execute the DAG.
        The executor uses the provided parameters and functions for execution.
    '''
    async def query_func(**kwargs):
        flat = learning_observer.communication_protocol.util.flatten(copy.deepcopy(query))
        output = await learning_observer.communication_protocol.executor.execute_dag(flat, parameters=kwargs, functions=FUNCTIONS)
        return output
    return query_func
