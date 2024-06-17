from learning_observer.stream_analytics.helpers import student_event_reducer


@student_event_reducer(null_state={"count": 0})
async def event_count(event, internal_state):
    '''
    An example of a per-student event counter
    '''
    state = {"count": internal_state.get('count', 0) + 1}

    return state, state
