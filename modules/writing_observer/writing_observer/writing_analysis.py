'''
This pipeline extracts high-level features from writing process data.

It just routes to smaller pipelines. Currently that's:
1) Time-on-task
2) Reconstruct text (+Deane graphs, etc.)
'''
# Necessary for the wrapper code below.
import datetime
import time
import re

import writing_observer.reconstruct_doc

import learning_observer.communication_protocol.integration
from learning_observer.stream_analytics.helpers import student_event_reducer, kvs_pipeline, KeyField, EventField, Scope
import learning_observer.settings
import learning_observer.util

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

# Threshold in seconds to determine if a student is actively working
ACTIVE_THRESHOLD = 60

# Here's the basic deal:
#
# - Our prototype didn't deal with multiple documents
# - We're still refactoring to do this fully
#
# For most development, it's still convenient to pretend there's only
# one document. For prototyping new writing dashboards, we need to get
# rid of this illusion. This is a toggle. We should move it to the
# config file, or we should refactor to fully eliminate the need.

student_scope = Scope([KeyField.STUDENT])

# This is a hack so we can flip for debugging to NOT managing documents
# correctly. That was for the original dashboard.
NEW = True

if NEW:
    gdoc_scope = Scope([KeyField.STUDENT, EventField('doc_id')])
else:
    gdoc_scope = student_scope  # HACK for backwards-compatibility


@learning_observer.communication_protocol.integration.publish_function('writing_observer.activity_map')
def determine_activity_status(last_ts):
    status = 'active' if time.time() - last_ts < ACTIVE_THRESHOLD else 'inactive'
    return {'status': status}


@kvs_pipeline(scope=gdoc_scope)
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
            'total_time_on_task': 0
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
        internal_state['total_time_on_task'] += delta_t
    return internal_state, internal_state


@kvs_pipeline(scope=gdoc_scope)
async def reconstruct(event, internal_state):
    '''
    This is a thin layer to route events to `reconstruct_doc` which compiles
    Google's deltas into a document. It also adds a bit of metadata e.g. for
    Deane plots.
    '''
    # If it's not a relevant event, ignore it
    if event['client']['event'] not in ["google_docs_save", "document_history"]:
        return False, False

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
    if learning_observer.settings.module_setting('writing_observer', 'verbose'):
        print(state)
    return state, state


@kvs_pipeline(scope=gdoc_scope, null_state={"count": 0})
async def event_count(event, internal_state):
    '''
    An example of a per-document pipeline
    '''
    if learning_observer.settings.module_setting('writing_observer', 'verbose'):
        print(event)

    state = {"count": internal_state.get('count', 0) + 1}

    return state, state


@kvs_pipeline(scope=gdoc_scope, null_state={})
async def awe_components(event, internal_state):
    '''
    An example of a per-document pipeline
    '''
    return False, False

@kvs_pipeline(scope=gdoc_scope, null_state={})
async def lt_process(event, internal_state):
    '''
    An example of a per-document pipeline
    '''
    return False, False


@kvs_pipeline(scope=student_scope, null_state={'timestamps': {}, 'last_document': ''})
async def document_access_timestamps(event, internal_state):
    '''
    We want to fetch documents around a certian time of day.
    We record the timestamp with a document id.

    Use case: a teacher wants to see the current version of
    the document their students had open at 10:45 AM

    NOTE we only keep that latest doc for each timestamp.
    Since we are in milliseconds, this should be okay.
    '''
    # If users switch between document tabs, then the system will
    # send mutliple `visibility` events from both tabs creating
    # more timestamps than we want. We skip those events.
    if event['client']['event'] in ['visibility']:
        return False, False

    document_id = get_doc_id(event)
    if document_id is not None:

        # if events dont have timestamps present, revert to right now
        # 'ts' metadata is in milliseconds while datetime.now is in seconds
        ts = event['client'].get('metadata', {}).get('ts', datetime.datetime.now().timestamp()*1000)

        if document_id != internal_state['last_document']:
            internal_state['timestamps'][ts] = document_id
            internal_state['last_document'] = document_id

        return internal_state, internal_state
    return False, False


@kvs_pipeline(scope=student_scope, null_state={'tags': {}})
async def document_tagging(event, internal_state):
    '''
    We would like to be able to group documents together to better work with
    multi-document workflows. For example, students may work in a graphic organizer
    or similar and then transition into their final draft.
    '''
    if event['client']['event'] not in ["document_history"]:
        return False, False

    document_id = get_doc_id(event)
    if document_id is not None:
        title = learning_observer.util.get_nested_dict_value(event, 'client.object.title', None)
        if title is None:
            return False, False
        tags = re.findall(r'#(\w+)', title)
        for tag in tags:
            if tag not in internal_state['tags']:
                internal_state['tags'][tag] = [document_id]
            elif document_id not in internal_state['tags'][tag]:
                internal_state['tags'][tag].append(document_id)
        return internal_state, internal_state
    return False, False


@kvs_pipeline(scope=student_scope, null_state={"docs": {}})
async def document_list(event, internal_state):
    '''
    We would like to gather a list of all Google Docs a student
    has visited / edited. In the future, we plan to add more metadata. This can
    then be used to decide which ones to show.
    '''
    document_id = get_doc_id(event)
    if document_id is not None:
        if "docs" not in internal_state:
            internal_state["docs"] = {}
        if document_id not in internal_state["docs"]:
            # In the future, we might include things like e.g. document title.
            internal_state["docs"][document_id] = {
            }
        # set title of document
        try:
            internal_state["docs"][document_id]["title"] = learning_observer.util.get_nested_dict_value(event, 'client.object.title')
        except KeyError:
            pass
        # set last time accessed
        if 'server' in event and 'time' in event['server']:
            internal_state["docs"][document_id]["last_access"] = event['server']['time']
        else:
            print("TODO: We got a bad event, and we should log this in some")
            print("way, or do similar recovery.")
        return internal_state, internal_state

    return False, False


@kvs_pipeline(scope=student_scope)
async def last_document(event, internal_state):
    '''
    Small bit of data -- the last document accessed. This can be extracted from
    `document_list`, but we don't need that level of complexity for the 1.0
    dashboard.

    This code accesses the code below which provides some hackish support
    functions for the analysis.  Over time these may age off with a better
    model.
    '''
    document_id = get_doc_id(event)

    if document_id is not None:
        state = {"document_id": document_id}
        return state, state

    return False, False


# Simple hack to match URLs.  This should probably be moved as well
# but for now it works.
#
# The URL for the main page looks as follows:
#  https://docs.google.com/document/u/0/?tgif=d
#
# Document URls are as follows:
#  https://docs.google.com/document/d/18JAnmxzVD_lGSfa8t6Se66KLZm30YFrC_4M-D2zdYG4/edit

DOC_URL_re = re.compile("^https://docs.google.com/document/d/(?P<DOCID>[^/\s]+)/(?P<ACT>[a-zA-Z]+)")  # noqa: W605 \s is invalid escape


def get_doc_id(event):
    """
    HACK: This is interim until we have more consistent events
    from the extension

    Some of the event types (e.g. 'google_docs_save') have
    a 'doc_id' which provides a link to the google document.
    Others, notably the 'visibility' and 'keystroke' events
    do not have doc_id but do have a link to an 'object'
    field which in turn contains an 'id' field linking to
    the google doc along with other features such as the
    title.  However other events (e.g. login & visibility)
    contain object links with id fields that do not
    correspond to a known doc.

    This method provides a simple abstraction that returns
    the 'doc_id' value if it exists or returns the 'id' from
    the 'object' field if it is present and if the url in
    the object field corresponds to a google doc id.

    We use the helper function for doc_url_p to test
    this.
    """

    client = event.get('client', {})
    doc_id = client.get('doc_id')
    if doc_id:
        return doc_id

    # Failing that pull out the url event.
    # Object_value = event.get('client', {}).get('object', None)
    url = client.get('object', {}).get('url')
    if not url:
        return None

    # Now test if the object has a URL and if that corresponds
    # to a doc edit/review URL as opposed to their main page.
    # if so return the id from it.  In the off chance the id
    # is still not present or is none then this will return
    # none.
    url_match = DOC_URL_re.match(url)
    if not url_match:
        return None

    doc_id = client.get('object', {}).get('id')
    return doc_id
