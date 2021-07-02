'''
This pipeline extracts high-level features from writing process data.

It just routes to smaller pipelines. Currently that's:
1) Time-on-task
2) Reconstruct text (+Deane graphs, etc.)
'''
from learning_observer.stream_analytics.helpers import kvs_pipeline
import writing_observer.reconstruct_doc

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


@kvs_pipeline()
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


@kvs_pipeline()
async def baseline_typing_speed(event, internal_state):
    '''
    Calculate baseline typing speed (characters per second for alphanumeric characters after the
    first character in a word). In our research results so far, this is an extremely reliable metric.
    Excluding word initial characters and nonalphanumeric keys eliminates pauses likely to be associated
    with most forms of metacognitive planning and deliberation, and so provides a relatively clean
    measure of typing speed.
    '''

    # We process keydown, but not keypress or keyup events.
    if 'keystroke' in event['client'] and event['client']['keystroke']['type'] != 'keydown':
        return internal_state, internal_state

    if internal_state is None:
        internal_state = {
            'saved_time': None,
            'saved_keycode': None,
            'total_inword_typing_time': 0,
            'nWordInternalKeystrokes': 0,
            'meanCharactersPerSecond': 0.0
        }

    # if 'event_type' in event['client'] and 'keystroke' in event['client']:
    #    print(event['client']['event_type'])
    #    print(event['client']['keystroke']['altKey'])
    #    print(event['client']['keystroke']['ctrlKey'])
    #    print(event['client']['keystroke']['keyCode'])
    #    print(event['client']['keystroke']['key'])

    last_time = internal_state['saved_time']
    last_keycode = internal_state['saved_keycode']
    internal_state['saved_time'] = event['client']['ts'] / 1000

    # Indentify in-word keypresses.
    # Exclude events that aren't keypresses.
    # Exclude keypresses combined with the alt or ctrl keys
    # Exclude nonalphanumeric characters, defined as anything other than A-Z, a-z, 0-9, or hyphen
    # (a better definion would allow internal apostrophes, and allow different types of
    # keycodes for variants of hyphen or apostrophe, but that's too complex to address
    # in the first instance.)
    # Exclude the first keypress after an excluded event
    if 'event_type' in event['client'] and event['client']['event_type'] == 'keypress' \
            and not event['client']['keystroke']['altKey'] and not event['client']['keystroke']['ctrlKey'] \
            and ((event['client']['keystroke']['keyCode'] > 47 and event['client']['keystroke']['keyCode'] < 91)
                 or event['client']['keystroke']['keyCode'] == 173):
        #print('updating the internal state')
        #print(last_keycode)
        internal_state['saved_keycode'] = event['client']['keystroke']['keyCode']
        if last_keycode is not None:
            internal_state['nWordInternalKeystrokes'] += 1
    # Reset keycode to None for non alphanumeric events.
    else:
        internal_state['saved_keycode'] = None

    # Initial conditions
    if last_time is None:
        last_time = internal_state['saved_time']

    # print(last_time,last_keycode)
    # Typing speed calculation based on assumption that events are reported in order
    # last_time None will exclude nonalphanumerics.
    # requiring keypress==down will make sure we only do interkey interval statistics
    # and we want to avoid any crazies from out of order events that would give us
    # negative times and thereby corrupt the speed measure
    if last_time is not None and last_keycode is not None and last_time <= internal_state['saved_time']:
        delta_t = min(
            TIME_ON_TASK_THRESHOLD,
            # Maximum time step
            internal_state['saved_time'] - last_time  # Time step
        )
        internal_state['total_inword_typing_time'] += delta_t
        internal_state['meanCharactersPerSecond'] = internal_state['nWordInternalKeystrokes'] / internal_state['total_inword_typing_time']
        # print('Total typing time: ' + str(internal_state['total_inword_typing_time']))
        # print('Current mean typing speed: ' + str(internal_state['meanCharactersPerSecond']))

    # Report out of order events
    if last_time > internal_state['saved_time']:
        print('Event at ' + str(last_time) + 'appeared out of order.')
    print(internal_state)

    return internal_state, internal_state


@kvs_pipeline()
async def reconstruct(event, internal_state):
    '''
    This is a thin layer to route events to `reconstruct_doc` which compiles
    Google's deltas into a document. It also adds a bit of metadata e.g. for
    Deane plots.
    '''
    #print(internal_state)

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


async def pipeline(metadata):
    '''
    We pass the event through all of our analytic pipelines, and
    combine the results into a common state-of-the-universe to return
    for display in the dashboard.
    '''
    processors = [time_on_task(metadata), reconstruct(metadata), baseline_typing_speed(metadata)]

    async def process(event):
        external_state = {}
        for processor in processors:
            external_state.update(await processor(event))
        return external_state
    return process
