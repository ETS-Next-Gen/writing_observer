'''
Module definition file

This may be an examplar for building new modules too.
'''

# Outgoing APIs
#
# Generically, these would usually serve JSON to dashboards written as JavaScript and
# HTML. These used to be called 'dashboards,' but we're now hosting those as static
# files.

import learning_observer.communication_protocol.query as q

from learning_observer import downloads as d

import writing_observer.aggregator
import writing_observer.writing_analysis
import writing_observer.languagetool
import writing_observer.tag_docs
import writing_observer.document_timestamps
from writing_observer.nlp_indicators import INDICATOR_JSONS


NAME = "The Writing Observer"

# things that process data versus things that interact with the environment
# side-effects or not
# course_id or rosters.course_id to distinguish or provide a default - how to specify selector
course_roster = q.call('learning_observer.courseroster')
process_texts = q.call('writing_observer.process_texts')
determine_activity = q.call('writing_observer.activity_map')
languagetool = q.call('writing_observer.languagetool')
update_via_google = q.call('writing_observer.update_reconstruct_with_google_api')
assignment_documents = q.call('google.fetch_assignment_docs')

unwind = q.call('unwind')
group_docs_by = q.call('writing_observer.group_docs_by')

document_access_ts = q.call('writing_observer.fetch_doc_at_timestamp')

source_selector = q.call('source_selector')


EXECUTION_DAG = {
    "execution_dag": {
        "roster": course_roster(runtime=q.parameter("runtime"), course_id=q.parameter("course_id", required=True)),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
        'update_docs': update_via_google(runtime=q.parameter("runtime"), doc_ids=q.variable('sources')),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("update_docs"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
        "docs_combined": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='provenance.provenance.STUDENT.value.user_id', RIGHT_ON='user_id'),
        'nlp': process_texts(writing_data=q.variable('docs'), options=q.parameter('nlp_options', required=False, default=[])),
        'nlp_combined': q.join(LEFT=q.variable('nlp'), LEFT_ON='provenance.provenance.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        'time_on_task': q.select(q.keys('writing_observer.time_on_task', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("sources"), RESOURCES_path='doc_id'), fields={'saved_ts': 'last_ts'}),
        'activity_map': q.map(determine_activity, q.variable('time_on_task'), value_path='last_ts'),
        'activity_combined': q.join(LEFT=q.variable('activity_map'), LEFT_ON='provenance.value.provenance.provenance.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        'single_student_latest_doc': q.select(q.keys('writing_observer.last_document', STUDENTS=q.parameter("student_id", required=True), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
        'single_update_doc': update_via_google(runtime=q.parameter('runtime'), doc_ids=q.variable('single_student_latest_doc')),
        'single_student_doc': q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.parameter("student_id", required=True), STUDENTS_path='user_id', RESOURCES=q.variable("single_update_doc"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
        'single_student_lt': languagetool(texts=q.variable('single_student_doc')),
        'single_lt_combined': q.join(LEFT=q.variable('single_student_lt'), LEFT_ON='provenance.provenance.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        'overall_lt': languagetool(texts=q.variable('docs')),
        'lt_combined': q.join(LEFT=q.variable('overall_lt'), LEFT_ON='provenance.provenance.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),

        'latest_doc_ids': q.join(LEFT=q.variable('roster'), RIGHT=q.variable('doc_ids'), LEFT_ON='user_id', RIGHT_ON='provenance.provenance.value.user_id'),
        # the following nodes are used to fetch a set of documents' metadata based on a given tag
        # HACK: this could be a lot fewer nodes with some form of filter functionality
        #  e.g. once we get the list of documents that match the inputted tag, we just filter
        #       the student document list on those
        #       instead we do some unwinding and joining to achieve filtering. this solution
        #       is a bit better suited for fetching document text which is how the system was
        #       initially built.
        'raw_tags': q.select(q.keys('writing_observer.document_tagging', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'), fields={'tags': 'tags'}),
        'unwind_tags': unwind(objects=q.variable('raw_tags'), value_path=q.parameter('tag_path', required=True), new_name='doc_id', keys_to_keep=['provenance']),
        'doc_list': q.select(q.keys('writing_observer.document_list', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'), fields={'docs': 'docs'}),
        'unwind_doc_list': unwind(objects=q.variable('doc_list'), value_path='docs', new_name='doc'),
        'tagged_doc_list': q.join(LEFT=q.variable('unwind_tags'), RIGHT=q.variable('unwind_doc_list'), LEFT_ON='doc_id', RIGHT_ON='doc.id'),
        'grouped_doc_list_by_student': group_docs_by(items=q.variable('tagged_doc_list'), value_path='provenance.provenance.value.user_id'),
        'tagged_docs_per_student': q.join(LEFT=q.variable('roster'), RIGHT=q.variable('grouped_doc_list_by_student'), LEFT_ON='user_id', RIGHT_ON='user_id'),

        # the following nodes just fetches docs related to an assignment on Google Classroom
        'assignment_docs': assignment_documents(runtime=q.parameter('runtime'), course_id=q.parameter('course_id', required=True), assignment_id=q.parameter('assignment_id', required=True)),

        # fetch the doc less than or equal to a timestamp
        'timestamped_docs': q.select(q.keys('writing_observer.document_access_timestamps', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'), fields={'timestamps': 'timestamps'}),
        'docs_at_ts': q.map(document_access_ts, values=q.variable('timestamped_docs'), value_path='timestamps', func_kwargs={'requested_timestamp': q.parameter('requested_timestamp')}),

        # figure out where to source document ids from
        # current options include `ts` for a given timestamp
        # or `latest` for the most recently accessed
        'sources': source_selector(sources={'ts': q.variable('docs_at_ts'), 'latest': q.variable('doc_ids')}, source=q.parameter('source', required=False, default='latest'))
    },
    "exports": {
        "docs_with_roster": {
            "returns": "docs_combined",
            "parameters": ["course_id"],
            "output": ""
        },
        "docs_with_nlp_annotations": {
            "returns": "nlp_combined",
            "parameters": ["course_id", "nlp_options"],
            "output": ""
        },
        "activity": {
            "returns": "activity_combined",
            "parameters": ["course_id"],
            "output": ""
        },
        'single_student': {
            'returns': 'single_lt_combined',
            'parameters': ['course_id', 'student_id'],
            'output': ''
        },
        'overall_errors': {
            'returns': 'lt_combined',
            'parameters': ['course_id'],
            'output': ''
        },
        'tagged_docs_per_student': {
            'returns': 'tagged_docs_per_student',
            'parameters': ['course_id', 'tag_path']
        },
        'assignment_docs': {
            'returns': 'assignment_docs',
            'parameters': ['course_id', 'assignment_id']
        },
        'latest_doc_ids': {
            'returns': 'latest_doc_ids',
            'parameters': ['course_id']
        }
    },
}

COURSE_AGGREGATORS = {
    "writing_observer": {
        "sources": [  # These are the reducers whose outputs we aggregate
            writing_observer.writing_analysis.time_on_task,
            writing_observer.writing_analysis.reconstruct
            # TODO: "roster"
        ],
        #  Then, we pass the per-student data through the cleaner, if provided.
        "cleaner": writing_observer.aggregator.sanitize_and_shrink_per_student_data,
        #  And we pass an array of the output of that through the aggregator
        "aggregator": writing_observer.aggregator.aggregate_course_summary_stats,
        "name": "This is the main Writing Observer dashboard.",
        # This is what we return for a student for whom we have no data
        # (or if we have data, don't have these fields)
        "default_data": {
            'writing_observer.writing_analysis.reconstruct': {
                'text': None,
                'position': 0,
                'edit_metadata': {'cursor': [2], 'length': [1]}
            },
            'writing_observer.writing_analysis.time_on_task': {
                'saved_ts': -1,
                'total_time_on_task': 0
            }
        }
    },
    "latest_data": {
        "sources": [
            writing_observer.writing_analysis.last_document
        ],
        "name": "Show the latest student writing",
        "aggregator": writing_observer.aggregator.latest_data
    }
}

STUDENT_AGGREGATORS = {
}

# Incoming event APIs
REDUCERS = [
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.gdoc_scope,
        'function': writing_observer.writing_analysis.time_on_task,
        'default': {'saved_ts': 0}
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.gdoc_scope,
        'function': writing_observer.writing_analysis.reconstruct,
        'default': {'text': ''}
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.student_scope,
        'function': writing_observer.writing_analysis.event_count
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.student_scope,
        'function': writing_observer.writing_analysis.document_list,
        'default': {'docs': []}
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.student_scope,
        'function': writing_observer.writing_analysis.last_document,
        'default': {'document_id': ''}
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.student_scope,
        'function': writing_observer.writing_analysis.document_tagging,
        'default': {'tags': {}}
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.student_scope,
        'function': writing_observer.writing_analysis.document_access_timestamps,
        'default': {'timestamps': {}}
    },
]


# Required client-side JavaScript downloads
THIRD_PARTY = {
    "require.js": d.REQUIRE_JS,
    "text.js": d.TEXT_JS,
    "r.js": d.R_JS,
    "bulma.min.css": d.BULMA_CSS,
    "fontawesome.js": d.FONTAWESOME_JS,
    "showdown.js": d.SHOWDOWN_JS,
    "showdown.js.map": d.SHOWDOWN_JS_MAP,
    "mustache.min.js": d.MUSTACHE_JS,
    "d3.v5.min.js": d.D3_V5_JS,
    "bulma-tooltip-min.css": d.BULMA_TOOLTIP_CSS
}


# We're still figuring this out, but we'd like to support hosting static files
# from the git repo of the module.
#
# This allows us to have a Merkle-tree style record of which version is deployed
# in our log files.
STATIC_FILE_GIT_REPOS = {
    'writing_observer': {
        # Where we can grab a copy of the repo, if not already on the system
        'url': 'https://github.com/ETS-Next-Gen/writing_observer.git',
        # Where the static files in the repo lie
        'prefix': 'modules/writing_observer/writing_observer/static',
        # Branches we serve. This can either be a whitelist (e.g. which ones
        # are available) or a blacklist (e.g. which ones are blocked)
        'whitelist': ['master']
    }
}

EXTRA_VIEWS = [{
    'name': 'NLP Options',
    'suburl': 'nlp-options',
    'static_json': INDICATOR_JSONS
}]
