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

import functools


def async_lambda(f):
    '''
    Work-around for how stupid Python 3 is about handling async
    functions. This turns a function into an asynchronous one. It
    allows us to make async lambda expressions.
    '''
    @functools.wraps(f)
    async def async_lambda_helper(*args, **kwargs):
        return f(*args, **kwargs)
    return async_lambda_helper


analytics_modules = {
    "org.mitros.mirror": {'event_processor': async_lambda(
        lambda metadata: async_lambda(lambda event: event)
    )},
}

try:
    import stream_analytics.dynamic_assessment
    analytics_modules.update({
        "org.mitros.dynamic-assessment": {
            'event_processor': async_lambda(
                lambda metadata: stream_analytics.dynamic_assessment.process_event
            )
        },
    })
except ModuleNotFoundError:
    print("Module dynamic_assessment not found. "
          "Starting without dynamic assessment")

try:
    import stream_analytics.writing_analysis
    analytics_modules.update({
        "org.mitros.writing-analytics": {
            'event_processor': stream_analytics.writing_analysis.pipeline
        }
    })
except ModuleNotFoundError:
    print("Module writing-analytics not found. "
          "Starting without writing analytics.")
