'''
This file defines reducers we wish to add to the incoming event
pipeline. The `learning_observer.stream_analytics` package includes
helper functions for Scoping the and setting the null state.
'''
import learning_observer.stream_analytics.time_on_task
from learning_observer.stream_analytics.helpers import student_event_reducer, kvs_pipeline, Scope, KeyField, EventField

page_scope = Scope([KeyField.STUDENT, EventField('page')])

@student_event_reducer(null_state={})
async def page_last_visited(event, internal_state):
    page = event['client'].get('page')
    if not page:
        return False, False
    internal_state[page] = event['server']['time']
    internal_state['last_visited'] = page
    return internal_state, internal_state


@kvs_pipeline(scope=page_scope, null_state={})
async def event_type_counter(event, internal_state):
    '''
    An example of a per-student event counter
    '''
    event_type = event['client']['event']
    if 'counts' not in internal_state:
        internal_state['counts'] = {}
    if event_type not in internal_state['counts']:
        internal_state['counts'][event_type] = 0
    internal_state['counts'][event_type] += 1

    return internal_state, internal_state


@kvs_pipeline(scope=page_scope)
async def time_on_task(event, internal_state):
    internal_state = learning_observer.stream_analytics.time_on_task.apply_time_on_task(
        internal_state,
        event['server']['time'],
        60
    )
    return internal_state, internal_state


@kvs_pipeline(scope=page_scope)
async def binned_time_on_task(event, internal_state):
    internal_state = learning_observer.stream_analytics.time_on_task.apply_binned_time_on_task(
        internal_state,
        event['server']['time'],
        60,
        600
    )
    return internal_state, internal_state


@kvs_pipeline(scope=page_scope, null_state={"events": []})
async def event_timeline(event, internal_state):
    """
    Collect a per-student timeline of events for later playback in dashboards.
    """
    client = event.get("client", {})
    event_type = client.get("event")
    metadata = client.get("metadata", {})
    timestamp = metadata.get("iso_ts")

    # Capture useful payload fields if present
    entry = {
        "event": event_type,
        "timestamp": timestamp,
        "id": client.get("id"),
        "scope": client.get("scope"),
    }

    # Add common payload values if they exist on the event
    for key in ("value", "submitCount", "correct", "message", "showAnswer"):
        if key in client:
            entry[key] = client[key]

    internal_state.setdefault("events", []).append(entry)
    return internal_state, internal_state
