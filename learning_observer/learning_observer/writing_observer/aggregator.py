import time


# What we return if there is no data...
DEFAULT_DATA = {
    'learning_observer.stream_analytics.writing_analysis.reconstruct': {
        'text': None,
        'position': 0,
        'edit_metadata': {'cursor': [2], 'length': [1]}
    },
    'learning_observer.stream_analytics.writing_analysis.time_on_task': {
        'saved_ts': -1,
        'total-time-on-task': 0
    }
}


def adhoc_writing_observer_clean(student_data):
    '''
    HACK HACK HACK HACK

    We:
    * Compute text length
    * Cut down the text to just what the client needs to receive (we
      don't want to send 30 full essays)

    This really needs to be made into part of a generic
    aggregator... But we're not there yet.

    TODO: Make aggregator, including these transformations on the
    teacher-facing dashboard end.
    '''
    text = student_data['learning_observer.stream_analytics.writing_analysis.reconstruct']['text']
    if text is None:
        student_data['writing-observer-compiled'] = {
            "text": "[None]",
            "character-count": 0
        }
        return student_data

    character_count = len(text)
    cursor_position = student_data['learning_observer.stream_analytics.writing_analysis.reconstruct']['position']

    # Compute the portion of the text we want to return.
    length = 103
    before = int(length * 2 / 3)
    # We step backwards and forwards from the cursor by the desired number of characters
    start = max(0, int(cursor_position - before))
    end = min(character_count - 1, start + length)
    # And, if we don't have much text after the cursor, we adjust the beginning
    # print(start, cursor_position, end)
    start = max(0, end - length)
    # Split on a word boundary, if there's one close by
    # print(start, cursor_position, end)
    while end < character_count and end - start < length + 10 and not text[end].isspace():
        end += 1

    # print(start, cursor_position, end)
    while start > 0 and end - start < length + 10 and not text[start].isspace():
        start -= 1

    # print(start, cursor_position, end)
    clipped_text = text[start:cursor_position - 1] + "❙" + text[max(cursor_position - 1, 0):end]
    # Yes, this does mutate the input. No, we should. No, it doesn't matter, since the
    # code needs to move out of here. Shoo, shoo.
    student_data['writing-observer-compiled'] = {
        "text": clipped_text,
        "character-count": character_count
    }
    # Remove things which are too big to send back. Note: Not benchmarked, so perhaps not too big
    del student_data['learning_observer.stream_analytics.writing_analysis.reconstruct']['text']
    # We should downsample, rather than removing
    del student_data['learning_observer.stream_analytics.writing_analysis.reconstruct']['edit_metadata']
    return student_data


def adhoc_writing_observer_aggregate(student_data):
    '''
    Compute and aggregate cross-classroom.
    '''
    max_idle_time = 0
    max_time_on_task = 0
    max_character_count = 0
    for student in student_data:
        max_character_count = max(
            max_character_count,
            student['writing-observer-compiled']['character-count']
        )
        max_time_on_task = max(
            max_time_on_task,
            student['learning_observer.stream_analytics.writing_analysis.time_on_task']["total-time-on-task"]
        )
    return {
        'max-character-count': max_character_count,
        'max-time-on-task': max_time_on_task,
        # TODO: Should we aggregate this in some way? If we run on multiple servers,
        # this is susceptible to drift. That could be jarring; even a few seconds
        # error could be an issue in some contexts.
        'current-time': time.time()
    }


