import time
import learning_observer.util


def sanitize_and_shrink_per_student_data(student_data):
    '''
    This function is run over the data for **each student**, one-by-one.

    We:
    * Compute text length
    * Cut down the text to just what the client needs to receive (we
      don't want to send 30 full essays)
    '''
    text = student_data.get('writing_observer.writing_analysis.reconstruct', {}).get('text', None)
    if text is None:
        student_data['writing_observer_compiled'] = {
            "text": "[None]",
            "character_count": 0
        }
        return student_data

    character_count = len(text)
    cursor_position = student_data['writing_observer.writing_analysis.reconstruct']['position']

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
    student_data['writing_observer_compiled'] = {
        "text": clipped_text,
        "character_count": character_count
    }
    # Remove things which are too big to send back. Note: Not benchmarked, so perhaps not too big
    del student_data['writing_observer.writing_analysis.reconstruct']['text']
    # We should downsample, rather than removing
    del student_data['writing_observer.writing_analysis.reconstruct']['edit_metadata']
    return student_data


def aggregate_course_summary_stats(student_data):
    '''
    Here, we compute summary stats across the entire course. This is
    helpful so that the front end can know, for example, how to render
    axes.

    Right now, this API is **evolving**. Ideally, we'd like to support:

    - Transforming summarized per-student data based on data from
      other students
    - Extract aggregates

    This API lets us do that, but it's a little too generic. We'd like
    to be a little bit more semantic.
    '''
    max_idle_time = 0
    max_time_on_task = 0
    max_character_count = 0
    for student in student_data:
        max_character_count = max(
            max_character_count,
            student.get('writing_observer_compiled', {}).get('character_count', 0)
        )
        max_time_on_task = max(
            max_time_on_task,
            student.get('writing_observer.writing_analysis.time_on_task', {}).get("total_time_on_task", 0)
        )
    return {
        "summary_stats": {
            'max_character_count': max_character_count,
            'max_time_on_task': max_time_on_task,
            # TODO: Should we aggregate this in some way? If we run on multiple servers,
            # this is susceptible to drift. That could be jarring; even a few seconds
            # error could be an issue in some contexts.
            'current_time': time.time()
        },
        "student_data": student_data
    }
