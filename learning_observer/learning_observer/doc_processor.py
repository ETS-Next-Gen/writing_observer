import aiohttp_session
import datetime

import learning_observer.constants
import learning_observer.google
import learning_observer.kvs
import learning_observer.offline
import learning_observer.run
import learning_observer.runtime
import learning_observer.auth.utils
import learning_observer.stream_analytics.helpers as sa_helpers

import writing_observer
import writing_observer.awe_nlp
import writing_observer.languagetool
import writing_observer.writing_analysis

def get_seconds_since_epoch():
    return datetime.datetime.now().timestamp()

'''
TODO add in desired rules.
Each rule should be a function that accepts
a document id.
Rules we want
- [x] document modified since last processing AND
      document not processed in last 5 minutes
- [ ] teacher visited dashboard recently
- [ ] events > 2*[events since last processed]
Start with just the first one
'''
async def check_recent_mod_and_not_recent_process(doc_id):
    '''Determine if the document has been altered since its last
    processing and check whether it is past a specified cutoff
    time (5 minutes).
    '''
    cutoff = 300 # 5 minutes
    student_id = await _determine_student(doc_id)
    key = sa_helpers.make_key(
        process_document,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    doc_info = await KVS[key]
    if doc_info is None: return True

    key = sa_helpers.make_key(
        writing_observer.writing_analysis.time_on_task,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    last_mod = await KVS[key]
    last_mod = last_mod['saved_ts']
    last_processed = doc_info['last_processed']
    now = get_seconds_since_epoch()
    recently_modified = last_mod > last_processed
    recently_processed = now - cutoff < last_processed
    if recently_modified and not recently_processed: return True
    return False


async def check_for_doc_fetch_failure(doc_id):
    '''Check if we should retry fetching a previously
    failed document fetch
    '''
    now = get_seconds_since_epoch()
    if doc_id in failed_fetch:
        last_try = failed_fetch[doc_id]
        if last_try > now - 300: return False
    return True


RULES = [
    check_recent_mod_and_not_recent_process,
    check_for_doc_fetch_failure
]

KVS = None
app = None
failed_fetch = {}

class MockApp:
    def __init__(self, loop):
        self.loop = loop

    def add_routes(self, *args):
        pass


class MockRequest(dict):
    pass


async def start():
    learning_observer.offline.init('creds.yaml')
    global app
    app = MockApp(asyncio.get_event_loop())
    learning_observer.google.initialize_and_register_routes(app)
    global KVS
    KVS = learning_observer.kvs.KVS()
    while True:
        doc_ids = await fetch_all_docs()
        await process_documents(doc_ids)
        # break


async def fetch_all_docs():
    '''Return a set of all doc ids currently available
    within the kvs.
    '''
    doc_ids = set()
    keys = await KVS.keys()
    doc_specifier = 'EventField.doc_id:'
    for k in keys:
        if doc_specifier not in k: continue
        end_of_specifier = k.find(doc_specifier) + len(doc_specifier)
        end_of_id = k.find(',', end_of_specifier)
        doc_id = k[end_of_specifier : end_of_id if end_of_id != -1 else len(k)]
        if doc_id == 'None': continue
        doc_ids.add(doc_id)
    return doc_ids


async def process_documents(docs):
    results = await asyncio.gather(*(process_document(d) for d in docs))


async def check_rules(rules, doc_id):
    '''Determine if a document passes all of the
    provided rules.
    '''
    for rule in rules:
        if not await rule(doc_id):
            return False
    return True


async def process_document(doc_id):
    if not await check_rules(RULES, doc_id):
        return
    print('* Starting to process document:', doc_id)
    student_id = await _determine_student(doc_id)
    google_auth = await _fetch_teacher_credentials(student_id)
    doc_text = await _fetch_document_text(doc_id, google_auth)
    if doc_text is None:
        print('  unable to fetch doc')
        failed_fetch[doc_id] = get_seconds_since_epoch()
        return
    failed_fetch.pop(doc_id, None)
    await _pass_doc_through_analysis(doc_id, doc_text, student_id)


async def _determine_student(doc_id):
    keys = await KVS.keys()
    matching_keys = [k for k in keys if doc_id in k]
    student_specifier = 'STUDENT:'
    students = [k[k.find(student_specifier) + len(student_specifier):] for k in matching_keys]
    # TODO handle more than 1 student per document, but for now just grab the first
    student = students[0]
    return student


async def _fetch_teacher_credentials(student):
    '''Determine which teacher a document belongs to
    and return the teacher's stored Google auth info
    '''
    keys = await KVS.keys()
    roster_specifier = 'learning_observer.google.roster'
    rosters = [k for k in keys if roster_specifier in k]
    matching_teachers = []
    for roster_key in rosters:
        roster = await KVS[roster_key]
        if student in roster['students']:
            matching_teachers.append(roster['teacher_id'])

    # TODO handle multiple teachers
    teacher = matching_teachers[0]
    auth_key = sa_helpers.make_key(
        learning_observer.auth.utils.google_stored_auth,
        {sa_helpers.KeyField.TEACHER: teacher},
        sa_helpers.KeyStateType.INTERNAL)
    creds = await KVS[auth_key]
    return creds


async def _fetch_document_text(doc_id, creds):
    '''Fetch the document text from the appropriate
    Google endpoint.
    '''
    async def get_session(request):
        return {learning_observer.constants.USER: {learning_observer.constants.USER_ID: '12345'}}

    aiohttp_session.get_session = get_session
    mock_request = MockRequest()
    mock_request[learning_observer.constants.AUTH_HEADERS] = creds
    mock_request[learning_observer.constants.USER] = {}
    mock_request.app = app
    runtime = learning_observer.runtime.Runtime(mock_request)
    response = await learning_observer.google.doctext(runtime, documentId=doc_id)
    if 'text' not in response:
        return None
    return response['text']


async def _pass_doc_through_analysis(doc_id, text, student_id):
    '''Pass the document text through a variety of
    analysis items. This includes,
    - Calculating all AWE components
    - Running through Language Tool
    Then store the documents in the default KVS
    '''
    awe_output = writing_observer.awe_nlp.process_text(text)
    prep_for_lt = [{'text': text, 'provenance': None}]
    lt_output = await writing_observer.languagetool.process_texts(prep_for_lt)
    output = {
        'document_id': doc_id,
        'student_id': student_id,
        'awe_components': awe_output,
        'languagetool': lt_output,
        'text': text,
        'last_processed': get_seconds_since_epoch()
    }
    # TODO choose a different function. since this is a separate
    # script, we get `Internal,__main__.process_document,...`
    key = sa_helpers.make_key(
        process_document,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    await KVS.set(key, output)


if __name__ == '__main__':
    import asyncio
    asyncio.run(start())
