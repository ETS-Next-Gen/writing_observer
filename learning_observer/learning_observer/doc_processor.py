import datetime

import learning_observer.google
import learning_observer.kvs
import learning_observer.offline
import learning_observer.run
import learning_observer.runtime

import writing_observer
import writing_observer.awe_nlp
import writing_observer.languagetool

'''
TODO add in desired rules.
Each rule should be a function that accepts
a document id.
Rules we want
- [ ] document modified since last processing AND
      document not processed in last 5 minutes
- [ ] teacher visited dashboard recently
- [ ] events > 2*[events since last processed]
Start with just the first one
'''
RULES = [
    lambda x: True
]

KVS = None

class mockApp:
    def add_routes(self, *args):
        pass


async def start():
    # FIXME something is missing where it doesn't register startup
    # functions in the modules folder.
    learning_observer.offline.init('creds.yaml')
    mock_app = mockApp()
    learning_observer.google.initialize_and_register_routes(mock_app)
    global KVS
    KVS = learning_observer.kvs.KVS()
    while True:
        doc_ids = await fetch_all_docs()
        await process_documents(doc_ids)
        break


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
        doc_id = k[end_of_specifier:k.find(',', end_of_specifier)]
        if doc_id == 'None': continue
        doc_ids.add(doc_id)
    return doc_ids


async def process_documents(docs):
    for doc_id in docs:
        print('processing document', doc_id)
        if check_rules(RULES, doc_id):
            await process_document(doc_id)


def check_rules(rules, doc_id):
    '''Determine if a document passes any of the
    provided rules.
    '''
    return any(rule(doc_id) for rule in rules)


async def process_document(doc_id):
    google_auth = await _fetch_proper_credentials(doc_id)
    doc_text = await _fetch_document_text(doc_id, google_auth)
    if doc_text is None:
        return
    await _pass_doc_through_analysis(doc_id, doc_text)


async def _fetch_proper_credentials(doc_id):
    '''Determine which teacher a document belongs to
    and return the teacher's stored Google auth info
    '''
    keys = await KVS.keys()
    matching_keys = [k for k in keys if doc_id in k]
    student_specifier = 'STUDENT:'
    students = [k[k.find(student_specifier) + len(student_specifier):] for k in matching_keys]
    # TODO handle more than 1 student per document, but for now just grab the first
    student = students[0]
    # TODO find teacher based on available rosters
    # TODO fetch teachers creds
    creds = None
    return creds


async def _fetch_document_text(doc_id, creds):
    '''Fetch the document text from the appropriate
    Google endpoint.
    '''
    # TODO I believe this needs an aiohttp_session to be present
    # not 100% sure what that looks like. I'll loop back
    # around to this
    mock_request = creds
    runtime = learning_observer.runtime.Runtime(mock_request)
    response = await learning_observer.google.doctext(runtime, documentId=doc_id)
    if 'text' not in response:
        return None
    return response['text']


async def _pass_doc_through_analysis(doc_id, text):
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
        'awe_components': awe_output,
        'languagetool': lt_output,
        'text': text,
        'last_modified': datetime.datetime.now()
    }
    # TODO store output in kvs


if __name__ == '__main__':
    import asyncio
    asyncio.run(start())
