'''
This pipeline extracts high-level features from writing process data.

It just routes to smaller pipelines. Currently that's:
1) Time-on-task
2) Reconstruct text (+Deane graphs, etc.)
'''
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


def time_on_task(time_threshold=TIME_ON_TASK_THRESHOLD):
    '''
    This adds up time intervals between successive timestamps. If the interval
    goes above some threshold, it adds that threshold instead (so if a student
    goes away for 2 hours without typing, we only add e.g. 5 minutes if
    `time_threshold` is set to 300.
    '''
    base_internal_state = {
        'saved_ts': None,
        'total-time-on-task': 0
    }

    taskkvs = kvs.KVS()
    async def process_event(event):
        internal_state = await taskkvs["writing-time-on-task"]
        if internal_state is None:
            internal_state = base_internal_state
        last_ts = internal_state['saved_ts']
        internal_state['saved_ts'] = event['server']['time']

        # Initial conditions
        if last_ts is None:
            last_ts = internal_state['saved_ts']
        if last_ts is not None:
            delta_t = min(time_threshold, internal_state['saved_ts']-last_ts)
            internal_state['total-time-on-task'] += delta_t
        await taskkvs.set("writing-time-on-task", internal_state)
        return internal_state
    return process_event


def reconstruct():
    '''
    This is a thin layer to route events to `reconstruct_doc` which compiles
    Google's deltas into a document. It returns a string-like object with
    additional metadata, such as cursor position and Deane graphs.
    '''
    #internal_state = {
    #    'doc': reconstruct_doc.google_text()
    #}
    taskkvs = kvs.KVS()

    async def process_event(event):
        json_rep = await taskkvs["writing-reconstruct"]
        internal_state = reconstruct_doc.google_text.from_json(json_rep=json_rep)
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
        await taskkvs.set("writing-reconstruct", internal_state.json)
        return internal_state.json
    return process_event


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
