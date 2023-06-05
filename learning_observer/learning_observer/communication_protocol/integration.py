'''
This file handles integrating queries into the
Learning Observer platform.
'''
import copy

import learning_observer.communication_protocol.executor
import learning_observer.communication_protocol.util

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
            flat = learning_observer.communication_protocol.util.flatten(copy.deepcopy(named_queries[query_name]))
            output = await learning_observer.communication_protocol.executor.execute_dag(flat, parameters=kwargs, functions=FUNCTIONS)
            return output
        if hasattr(module, query_name):
            raise AttributeError(f'Attibute, {query_name}, already exists under {module.__name__}')
        else:
            setattr(module, query_name, query_func)


def create_function(query):
    async def query_func(**kwargs):
        flat = learning_observer.communication_protocol.util.flatten(copy.deepcopy(query))
        output = await learning_observer.communication_protocol.executor.execute_dag(flat, parameters=kwargs, functions=FUNCTIONS)
        return output
    return query_func
