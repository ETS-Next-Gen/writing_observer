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

STUDENT_REDUCER_MODULES = None


def student_reducer_modules():
    '''
    Helper.

    TODO: Somewhat obsolete, since a lot of this code will migrate into module_loader.
    '''
    global STUDENT_REDUCER_MODULES
    return STUDENT_REDUCER_MODULES


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
    srm['org.mitros.mirror'].append({'student_event_reducer': async_lambda(
        lambda metadata: async_lambda(lambda event: event)
    )})
    try:
        import learning_observer.stream_analytics.dynamic_assessment
        srm["org.mitros.dynamic-assessment"].append({
            'student_event_reducer': async_lambda(
                lambda metadata: learning_observer.stream_analytics.dynamic_assessment.process_event
            )
        })
    except ModuleNotFoundError:
        print("Module dynamic_assessment not found. "
              "Starting without dynamic assessment")

    try:
        import learning_observer.stream_analytics.writing_analysis
        srm["org.mitros.writing-analytics"].append({
            'student_event_reducer': learning_observer.stream_analytics.writing_analysis.pipeline
        })
    except ModuleNotFoundError:
        print("Module writing-analytics not found. "
              "Starting without writing analytics.")

    reducers = learning_observer.module_loader.reducers()
    for reducer in reducers:
        context = reducer['context']
        function = reducer['function']
        srm[context].append({
            'student_event_reducer': function
        })

    global STUDENT_REDUCER_MODULES
    STUDENT_REDUCER_MODULES = dict(srm)
