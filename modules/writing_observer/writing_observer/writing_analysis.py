'''
This pipeline extracts high-level features from writing process data.

It just routes to smaller pipelines. Currently that's:
1) Time-on-task
2) Reconstruct text (+Deane graphs, etc.)
'''
import writing_observer.reconstruct_doc

from learning_observer.stream_analytics.helpers import student_event_reducer, kvs_pipeline, KeyField, EventField, Scope

# How do we count the last action in a document? If a student steps away
# for hours, we don't want to count all those hours.
#
# We might e.g. assume a one minute threshold. If students are idle
# for more than a minute, we count one minute. If less, we count the
# actual time spent. So if a student goes away for an hour, we count
# that as one minute. This threshold sets that maximum. For debugging,
# a few seconds is convenient. For production use, 60-300 seconds (or
# 1-5 minutes) might be more reasonable.
#
# In edX, for time-on-task calculations, the exact threshold had a
# surprisingly small impact on any any sort of interpretation
# (e.g. all the numbers would go up/down 20%, but behavior was
# substantatively identical).

# Should be 60-300 in prod. 5 seconds is nice for debugging
TIME_ON_TASK_THRESHOLD = 5


gdoc_scope = Scope([KeyField.STUDENT, EventField('doc_id')])
student_scope = Scope([KeyField.STUDENT])


@kvs_pipeline(scope=student_scope)
async def time_on_task(event, internal_state):
    '''
    This adds up time intervals between successive timestamps. If the interval
    goes above some threshold, it adds that threshold instead (so if a student
    goes away for 2 hours without typing, we only add e.g. 5 minutes if
    `time_threshold` is set to 300.
    '''
    if internal_state is None:
        internal_state = {
            'saved_ts': None,
            'total-time-on-task': 0
        }
    last_ts = internal_state['saved_ts']
    internal_state['saved_ts'] = event['server']['time']

    # Initial conditions
    if last_ts is None:
        last_ts = internal_state['saved_ts']
    if last_ts is not None:
        delta_t = min(
            TIME_ON_TASK_THRESHOLD,               # Maximum time step
            internal_state['saved_ts'] - last_ts  # Time step
        )
        internal_state['total-time-on-task'] += delta_t
    return internal_state, internal_state


@kvs_pipeline(scope=gdoc_scope)
async def reconstruct(event, internal_state):
    '''
    This is a thin layer to route events to `reconstruct_doc` which compiles
    Google's deltas into a document. It also adds a bit of metadata e.g. for
    Deane plots.
    '''
    # If it's not a relevant event, ignore it
    if event['client']['event'] not in ["google_docs_save", "document_history"]:
        return False, False

    internal_state = writing_observer.reconstruct_doc.google_text.from_json(
        json_rep=internal_state)
    if event['client']['event'] == "google_docs_save":
        bundles = event['client']['bundles']
        for bundle in bundles:
            internal_state = writing_observer.reconstruct_doc.command_list(
                internal_state, bundle['commands']
            )
    elif event['client']['event'] == "document_history":
        change_list = [
            i[0] for i in event['client']['history']['changelog']
        ]
        internal_state = writing_observer.reconstruct_doc.command_list(
            writing_observer.reconstruct_doc.google_text(), change_list
        )
    state = internal_state.json
    print(state)
    return state, state


@kvs_pipeline(scope=gdoc_scope)
async def event_count(event, internal_state):
    '''
    An example of a per-document pipeline
    '''
    print("I'm getting called!")
    print(event)

    state = {"status": "called"}

    return state, state


@kvs_pipeline(scope=student_scope, null_state={})
async def document_list(event, internal_state):
    '''
    We would like to gather a list of all Google Docs a student
    has visited / edited. This can then be used to decide which
    ones to show.
    '''
    document_id = event.get('client', {}).get('doc_id', None)

    if document_id is not None:
        if document_id not in internal_state:
            # In the future, we might include things like e.g. document title.
            internal_state[document_id] = {}
            return internal_state, internal_state

    return False, False
