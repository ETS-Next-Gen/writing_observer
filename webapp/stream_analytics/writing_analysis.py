'''
This pipeline extracts high-level features from writing process data.

It just routes to smaller pipelines. Currently that's:
1) Time-on-task
2) Reconstruct text (+Deane graphs, etc.)
'''
import functools

import kvs

import stream_analytics.reconstruct_doc as reconstruct_doc

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


def kvs_pipeline(namespace):
    '''
    Closures, anyone?

    There's a bit to unpack here.
    '''
    def decorator(func):
        '''
        Top-level function. This allows us to configure the decorator (and
        returns the decorator)
        '''
        @functools.wraps(func)
        def wrapper_closure():
            '''
            The decorator itself. We create a function that, when called,
            creates an event processing pipeline. It keeps a pointer
            to the KVS inside of the closure. This way, each pipeline has
            its own KVS. This is the level at which we want consistency,
            want to allow sharding, etc. If two users are connected, each
            will have their own data store connection.
            '''
            taskkvs = kvs.KVS()
            async def process_event(events):
                '''
                This is the function which processes events. It calls the event
                processor, passes in the event(s) and state. It takes
                the internal state and the external state from the
                event processor. The internal state goes into the KVS
                for use in the next call, while the external state
                returns to the dashboard.

                The external state should include everything needed
                for the dashboard visualization and exclude anything
                large or private. The internal state needs everything
                needed to continue reducing the events.
                '''
                internal_state = await taskkvs[namespace]
                internal_state, external_state = await func(events, internal_state)
                await taskkvs.set(namespace, internal_state)
                return external_state
            return process_event
        return wrapper_closure
    return decorator


@kvs_pipeline("writing-time-on-task")
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
        delta_t = min(TIME_ON_TASK_THRESHOLD, internal_state['saved_ts']-last_ts)
        internal_state['total-time-on-task'] += delta_t
    return internal_state, internal_state


@kvs_pipeline("reconstruct-writing")
async def reconstruct(event, internal_state):
    '''
    This is a thin layer to route events to `reconstruct_doc` which compiles
    Google's deltas into a document. It also adds a bit of metadata e.g. for
    Deane plots.
    '''
    internal_state = reconstruct_doc.google_text.from_json(json_rep=internal_state)
    if event['client']['event'] == "google_docs_save":
        bundles = event['client']['bundles']
        for bundle in bundles:
            internal_state = reconstruct_doc.command_list(
                internal_state, bundle['commands']
            )
    elif event['client']['event'] == "document_history":
        change_list = [
            i[0] for i in event['client']['history']['changelog']
        ]
        internal_state = reconstruct_doc.command_list(
            reconstruct_doc.google_text(), change_list
        )
    state = internal_state.json
    return state, state


def pipeline():
    '''
    We pass the event through all of our analytic pipelines, and
    combine the results into a common state-of-the-universe to return
    for display in the dashboard.
    '''
    processors = [time_on_task(), reconstruct()]

    async def process(event):
        external_state = {}
        for processor in processors:
            external_state.update(await processor(event))
        return external_state
    return process
