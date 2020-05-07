'''
This pipeline extracts high-level features from writing process data.
'''
import reconstruct_doc

# How do we count the last action in a document?
#
# We will assume a one minute threshold. If students are idle
# for more than a minute, we count one minute. If less, we count the
# actual time spent. So if a student goes away for an hour, we count
# that as one minute.
#
# In edX, for time-on-task calculations, the exact threshold had a
# surprisingly small impact on any any sort of interpretation
# (e.g. all the numbers would go up/down 20%, but behavior was
# substantatively identical).

TIME_ON_TASK_THRESHOLD = 5  # Should be 60-300 in prod. 5 seconds is nice for debugging

def time_on_task(time_threshold=TIME_ON_TASK_THRESHOLD):
    state = {
        'ts': None,
        'last-ts': None,
        'total-time-on-task': 0
    }

    def process_event(event):
        state['last-ts'] = state['ts']
        state['ts'] = event['server']['time']

        # Initial conditions
        if state['last-ts'] is None:
            state['last-ts'] = state['ts']
        if state['last-ts'] is not None:
            delta_t = min(time_threshold, state['ts']-state['last-ts'])
            state['total-time-on-task'] += delta_t
        return state
    return process_event

def reconstruct():
    state = {
        'doc': reconstruct_doc.google_text()
    }
    def process_event(event):
        if event['client']['event'] == "google_docs_save":
            bundles = event['client']['bundles']
            for bundle in bundles:
                state['doc'] = reconstruct_doc.command_list(state['doc'], bundle['commands'])
        elif event['client']['event'] == "document_history":
            change_list = [i[0] for i in event['client']['history']['changelog']]
            state['doc'] = reconstruct_doc.command_list(reconstruct_doc.google_text(), change_list)
        return state['doc'].json
    return process_event

def pipeline():
    processors = [time_on_task(), reconstruct()]
    def process(event):
        state = {}
        for processor in processors:
            state.update(processor(event))
        return state
    return process
