import sys
import time

import learning_observer.settings
import learning_observer.stream_analytics.helpers
import learning_observer.util


def excerpt_active_text(
    text, cursor_position,
    desired_length=103, cursor_target=2 / 3, max_overflow=10,
    cursor_character="❙"
):
    '''
    This function returns a short segment of student text, cutting in a
    sensible way around word boundaries. This can be used for real-time
    typing views.

    `desired_length` is how much text we want.
    `cursor_target` is what fraction of the text should be before the cursor.
    `max_overflow` is how much longer we're willing to go in order to land on
       a word boundary.
    `cursor_character` is what we insert at the boundary. Can be an empty
       string, a nice bit of markup, etc.
    '''
    character_count = len(text)
    before = int(desired_length * 2 / 3)
    # We step backwards and forwards from the cursor by the desired number of characters
    start = max(0, int(cursor_position - before))
    end = min(character_count - 1, start + desired_length)
    # And, if we don't have much text after the cursor, we adjust the beginning
    # print(start, cursor_position, end)
    start = max(0, end - desired_length)
    # Split on a word boundary, if there's one close by
    # print(start, cursor_position, end)
    while end < character_count and end - start < desired_length + 10 and not text[end].isspace():
        end += 1

    # print(start, cursor_position, end)
    while start > 0 and end - start < desired_length + 10 and not text[start].isspace():
        start -= 1

    clipped_text = text[start:max(cursor_position - 1, 0)] + cursor_character + text[max(cursor_position - 1, 0):end]
    return clipped_text


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

    # Yes, this does mutate the input. No, we should. No, it doesn't matter, since the
    # code needs to move out of here. Shoo, shoo.
    student_data['writing_observer_compiled'] = {
        "text": excerpt_active_text(text, cursor_position),
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
        }
    }


######
#
#  Everything from here on is a hack.
#  We need to figure out proper abstractions.
#
######


async def get_latest_student_documents(student_data):
    '''
    This will retrieve the latest student documents from the database. It breaks
    abstractions.
    '''
    import learning_observer.kvs

    import writing_observer.writing_analysis
    from learning_observer.stream_analytics.fields import KeyField, KeyStateType, EventField

    kvs = learning_observer.kvs.KVS()

    document_keys = ([
        learning_observer.stream_analytics.helpers.make_key(
            writing_observer.writing_analysis.reconstruct,
            {
                KeyField.STUDENT: s['user_id'],
                EventField('doc_id'): s.get('writing_observer.writing_analysis.last_document', {}).get('document_id', None)
            },
            KeyStateType.INTERNAL
        ) for s in student_data if 'writing_observer.writing_analysis.last_document' in s])

    #print(">>> DOC KEYS")
    #print(document_keys)
    
    writing_data = await kvs.multiget(keys=document_keys)

    #print(">> WRITING DATA", writing_data)
    
    # Return blank entries if no data, rather than None. This makes it possible
    # to use item.get with defaults sanely.
    writing_data = [{} if item is None else item for item in writing_data]

    #print("WRITING DATA >>>>")
    #print(writing_data)
    
    return writing_data


async def remove_extra_data(writing_data):
    '''
    We don't want Deane graph data going to the client. We just do a bit of
    a cleanup. This is in-place.
    '''
    for item in writing_data:
        if 'edit_metadata' in item:
            del item['edit_metadata']
    return writing_data


async def merge_with_student_data(writing_data, student_data):
    '''
    Add the student metadata to each text
    '''
    for item, student in zip(writing_data, student_data):
        if 'edit_metadata' in item:
            del item['edit_metadata']
        item['student'] = student
    return writing_data


if learning_observer.settings.module_setting('writing_observer', 'use_nlp', False):
    try:
        import writing_observer.awe_nlp
        processor = writing_observer.awe_nlp.process_texts
    except ImportError as e:
        print(e)
        print('AWE Components is not installed. To install, please see https://github.com/ETS-Next-Gen/AWE_Components')
        sys.exit(-1)
else:
    import writing_observer.stub_nlp
    processor = writing_observer.stub_nlp.process_texts


async def latest_data(student_data, options=None):
    '''
    HACK HACK HACK

    I just hardcoded this, breaking abstractions, repeating code, etc.
    '''
    writing_data = await get_latest_student_documents(student_data)
    writing_data = await remove_extra_data(writing_data)
    writing_data = await merge_with_student_data(writing_data, student_data)

    #print(">>>> PRINT WRITE DATA.")
    #print(writing_data)

    just_the_text = [w.get("text", "") for w in writing_data]

    #print(">>>> PRINT just.")
    #print(just_the_text)

    annotated_texts = await writing_observer.awe_nlp.process_texts_parallel(just_the_text)

    #print(">>>> PRINT ANN TXT.")
    #print(annotated_texts)

    
    for annotated_text, single_doc in zip(annotated_texts, writing_data):
        if annotated_text != "Error":
            single_doc.update(annotated_text)
    # Call Paul's code to add stuff to it
    return {'latest_writing_data': writing_data}
