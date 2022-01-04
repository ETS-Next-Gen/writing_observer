'''
Although the target is writing analytics, we would like analytics
to eventually have pluggable modules. To validate that we're
maintaining with the right abstractions in place, we are developing
around several streaming systems:

* Dynamic assessment
* Writing process analytics
* Mirror

This should move into a config file.
'''

import collections
import functools
import learning_observer.module_loader

REDUCER_MODULES = None


def reducer_modules():
    '''
    Helper.

    TODO: Somewhat obsolete, since a lot of this code will migrate into module_loader.
    '''
    global REDUCER_MODULES
    return REDUCER_MODULES


def async_lambda(function):
    '''Work-around for Python 3 issues with handling async
    functions. This turns a function into an asynchronous one. It
    allows us to make async lambda expressions.
    '''
    @functools.wraps(function)
    async def async_lambda_helper(*args, **kwargs):
        '''
        The async version of our lambda
        '''
        return function(*args, **kwargs)
    return async_lambda_helper


def init():
    import learning_observer.module_loader
    srm = collections.defaultdict(lambda: list())

    # For debugging; this can go away at some point
    srm['org.mitros.mirror'].append({'reducer': async_lambda(
        lambda metadata: async_lambda(lambda event: event)
    )})

    reducers = learning_observer.module_loader.reducers()
    for reducer in reducers:
        context = reducer['context']
        function = reducer['function']
        scope = reducer.get('scope', helpers.FieldSet([helpers.KeyField.STUDENT]))
        srm[context].append({
            'reducer': function,
            'scope': scope
        })

    global REDUCER_MODULES
    REDUCER_MODULES = dict(srm)
