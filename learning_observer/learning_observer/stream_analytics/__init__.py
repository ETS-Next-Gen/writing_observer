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


def async_lambda(f):
    '''Work-around for Python 3 issues with handling async
    functions. This turns a function into an asynchronous one. It
    allows us to make async lambda expressions.
    '''
    @functools.wraps(f)
    async def async_lambda_helper(*args, **kwargs):
        return f(*args, **kwargs)
    return async_lambda_helper

student_reducer_modules = None


def init():
    srm = collections.defaultdict(lambda:list())
    srm['org.mitros.mirror'].append({'student_event_reducer': async_lambda(
        lambda metadata: async_lambda(lambda event: event)
    )})
    try:
        import stream_analytics.dynamic_assessment
        srm["org.mitros.dynamic-assessment"].append({
            'student_event_reducer': async_lambda(
                lambda metadata: stream_analytics.dynamic_assessment.process_event
            )
        })
    except ModuleNotFoundError:
        print("Module dynamic_assessment not found. "
              "Starting without dynamic assessment")

    try:
        import stream_analytics.writing_analysis
        srm["org.mitros.writing-analytics"].append({
            'student_event_reducer': stream_analytics.writing_analysis.pipeline
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

    global student_reducer_modules
    student_reducer_modules = dict(srm)
