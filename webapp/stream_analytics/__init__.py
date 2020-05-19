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

analytics_modules = {
    "org.mitros.mirror": {'event_processor': lambda x: x},
}

try:
    import stream_analytics.dynamic_assessment
    analytics_modules.update({
        "org.mitros.dynamic-assessment": {
            'event_processor': stream_analytics.dynamic_assessment.process_event
        },
    })
except ModuleNotFoundError:
    print("Module dynamic_assessment not found. "
          "Starting without dynamic assessment")

try:
    import stream_analytics.writing_analysis
    analytics_modules.update({
        "org.mitros.writing-analytics": {
            'event_processor': stream_analytics.writing_analysis.pipeline()
        }
    })
except ModuleNotFoundError:
    print("Module writing-analytics not found. "
          "Starting without writing analytics.")
