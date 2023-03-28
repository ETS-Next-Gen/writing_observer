from abc import ABC, abstractmethod
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


def aggregate_course_summary_stats(request, student_data):
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


def get_last_document_id(s):
    """
    Retrieves the ID of the latest document for a given student.

    :param s: The student data.
    :return: The ID of the latest document.
    """
    return s.get('writing_observer.writing_analysis.last_document', {}).get('document_id', None)


async def remove_extra_data(writing_data):
    """
    Removes Deane graph data from writing data.

    :param writing_data: The writing data to process.
    :return: The processed writing data.
    """
    for item in writing_data:
        if 'edit_metadata' in item:
            del item['edit_metadata']
    return writing_data


async def merge_with_student_data(writing_data, student_data):
    """
    Merges writing data with student metadata.

    :param writing_data: The writing data to merge.
    :param student_data: The student metadata to merge.
    :return: The merged writing data.
    """
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


class StudentDocumentRetriever(ABC):
    """
    Abstract base class for retrieving student documents.
    """

    @abstractmethod
    async def retrieve_latest_documents(self, student_data, **kwargs):
        """
        Retrieves the latest documents for a set of students.

        :param student_data: The student data.
        :param kwargs: Additional arguments.
        :return: The latest documents.
        """
        pass


class KVSStudentDocumentRetriever(StudentDocumentRetriever):
    """
    Retrieves student documents from KVS.
    """

    async def retrieve_latest_documents(self, student_data):
        """
        Retrieves the latest documents for a set of students from KVS.

        :param student_data: The student data.
        :return: The latest documents.
        """
        import learning_observer.kvs
        import writing_observer.writing_analysis
        from learning_observer.stream_analytics.fields import KeyField, KeyStateType, EventField

        kvs = learning_observer.kvs.KVS()

        # To do: Handle students with no documents more cleanly.
        #
        # Right now, we just return a key with the text 'None', which is an
        # an invalid document.
        document_keys = ([
            learning_observer.stream_analytics.helpers.make_key(
                writing_observer.writing_analysis.reconstruct,
                {
                    KeyField.STUDENT: s['user_id'],
                    EventField('doc_id'): get_last_document_id(s)
                },
                KeyStateType.INTERNAL
            ) for s in student_data])

        writing_data = await kvs.multiget(keys=document_keys)

        # Return blank entries if no data, rather than None. This makes it possible
        # to use item.get with defaults sanely.
        writing_data = [{} if item is None else item for item in writing_data]
        return writing_data


class GoogleStudentDocumentRetriever(StudentDocumentRetriever):
    def __init__(self, request):
        """
        Initializes a new instance of the GoogleStudentDocumentRetriever class.

        :param request: The request to use for retrieving Google documents.
        """
        self.request = request

    async def retrieve_latest_documents(self, student_data):
        """
        Retrieves the latest documents for a set of students using Google Docs.

        :param student_data: The student data.
        :return: The latest documents.
        """
        import learning_observer.google

        writing_data = [
            {'text': await learning_observer.google.doctext(self.request, documentId=get_last_document_id(s))}
            if get_last_document_id(s) is not None else {}
            for s in student_data
        ]
        return writing_data


async def latest_data(request, student_data, options=None):
    """
    Retrieves the latest writing data for a set of students.

    :param request: The request to use for retrieving Google documents.
    :param student_data: The student data.
    :param options: Additional options to pass to the text processing pipeline.
    :return: The latest writing data.
    """
    student_document_retriever = None

    if learning_observer.settings.module_setting('writing_observer', 'use_google_documents', True):
        student_document_retriever = GoogleStudentDocumentRetriever(request)
    else:
        student_document_retriever = KVSStudentDocumentRetriever()

    writing_data = await student_document_retriever.retrieve_latest_documents(student_data)
    writing_data = await remove_extra_data(writing_data)
    writing_data = await merge_with_student_data(writing_data, student_data)
    writing_data = await processor(writing_data, options)
    return {'latest_writing_data': writing_data}
