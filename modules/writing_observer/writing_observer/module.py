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

import writing_observer.aggregator
import writing_observer.writing_analysis
import writing_observer.languagetool
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


EXECUTION_DAG = {
    "execution_dag": {
        "roster": course_roster(runtime=q.parameter("runtime"), course_id=q.parameter("course_id", required=True)),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
        'update_docs': update_via_google(runtime=q.parameter("runtime"), doc_ids=q.variable('doc_ids')),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("update_docs"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
        "docs_combined": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='providence.providence.STUDENT.value.user_id', RIGHT_ON='user_id'),
        'nlp': process_texts(writing_data=q.variable('docs'), options=q.parameter('nlp_options', required=False, default=[])),
        'nlp_combined': q.join(LEFT=q.variable('nlp'), LEFT_ON='providence.providence.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        'time_on_task': q.select(q.keys('writing_observer.time_on_task', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'saved_ts': 'last_ts'}),
        'activity_map': q.map(determine_activity, q.variable('time_on_task'), value_path='last_ts'),
        'activity_combined': q.join(LEFT=q.variable('activity_map'), LEFT_ON='providence.value.providence.providence.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        'single_student_latest_doc': q.select(q.keys('writing_observer.last_document', STUDENTS=q.parameter("student_id", required=True), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
        'single_update_doc': update_via_google(runtime=q.parameter('runtime'), doc_ids=q.variable('single_student_latest_doc')),
        'single_student_doc': q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.parameter("student_id", required=True), STUDENTS_path='user_id', RESOURCES=q.variable("single_update_doc"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
        'single_student_lt': languagetool(texts=q.variable('single_student_doc')),
        'single_lt_combined': q.join(LEFT=q.variable('single_student_lt'), LEFT_ON='providence.providence.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        'overall_lt': languagetool(texts=q.variable('docs')),
        'lt_combined': q.join(LEFT=q.variable('overall_lt'), LEFT_ON='providence.providence.STUDENT.value.user_id', RIGHT=q.variable('roster'), RIGHT_ON='user_id')
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
        'function': writing_observer.writing_analysis.document_list
    },
    {
        'context': "org.mitros.writing_analytics",
        'scope': writing_observer.writing_analysis.student_scope,
        'function': writing_observer.writing_analysis.last_document,
        'default': {'document_id': ''}
    }
]


# Required client-side JavaScript downloads
THIRD_PARTY = {
    "require.js": {
        "url": "https://requirejs.org/docs/release/2.3.6/comments/require.js",
        "hash": "d1e7687c1b2990966131bc25a761f03d6de83115512c9ce85d72e4b9819fb"
        "8733463fa0d93ca31e2e42ebee6e425d811e3420a788a0fc95f745aa349e3b01901"
    },
    "text.js": {
        "url": "https://raw.githubusercontent.com/requirejs/text/"
        "3f9d4c19b3a1a3c6f35650c5788cbea1db93197a/text.js",
        "hash": "fb8974f1633f261f77220329c7070ff214241ebd33a1434f2738572608efc"
        "8eb6699961734285e9500bbbd60990794883981fb113319503208822e6706bca0b8"
    },
    "r.js": {
        "url": "https://requirejs.org/docs/release/2.3.6/r.js",
        "hash": "52300a8371df306f45e981fd224b10cc586365d5637a19a24e710a2fa566f"
        "88450b8a3920e7af47ba7197ffefa707a179bc82a407f05c08508248e6b5084f457"
    },
    "bulma.min.css": {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.0/css/"
        "bulma.min.css",
        "hash": "ec7342883fdb6fbd4db80d7b44938951c3903d2132fc3e4bf7363c6e6dc52"
        "95a478c930856177ac6257c32e1d1e10a4132c6c51d194b3174dc670ab8d116b362"
    },
    "fontawesome.js": {
        "url": "https://use.fontawesome.com/releases/v5.3.1/js/all.js",
        "hash": "83e7b36f1545d5abe63bea9cd3505596998aea272dd05dee624b9a2c72f96"
        "62618d4bff6e51fafa25d41cb59bd97f3ebd72fd94ebd09a52c17c4c23fdca3962b"
    },
    "showdown.js": {
        "url": "https://rawgit.com/showdownjs/showdown/1.9.1/dist/showdown.js",
        "hash": "4fe14f17c2a1d0275d44e06d7e68d2b177779196c6d0c562d082eb5435eec"
        "4e710a625be524767aef3d9a1f6a5b88f912ddd71821f4a9df12ff7dd66d6fbb3c9"
    },
    "showdown.js.map": {
        "url": "https://rawgit.com/showdownjs/showdown/1.9.1/dist/showdown.js.map",
        "hash": "74690aa3cea07fd075942ba9e98cf7297752994b93930acb3a1baa2d3042a"
        "62b5523d3da83177f63e6c02fe2a09c8414af9e1774dad892a303e15a86dbeb29ba"
    },
    "mustache.min.js": {
        "url": "http://cdnjs.cloudflare.com/ajax/libs/mustache.js/3.1.0/"
        "mustache.min.js",
        "hash": "e7c446dc9ac2da9396cf401774efd9bd063d25920343eaed7bee9ad878840"
        "e846d48204d62755aede6f51ae6f169dcc9455f45c1b86ba1b42980ccf8f241af25"
    },
    "d3.v5.min.js": {
        "url": "https://d3js.org/d3.v5.min.js",
        "hash": "466fe57816d719048885357cccc91a082d8e5d3796f227f88a988bf36a5c2"
        "ceb7a4d25842f5f3c327a0151d682e648cd9623bfdcc7a18a70ac05cfd0ec434463"
    },
    "bulma-tooltip-min.css": {
        "url": "https://cdn.jsdelivr.net/npm/@creativebulma/bulma-tooltip@1.2.0/"
        "dist/bulma-tooltip.min.css",
        "hash": "fc37b25fa75664a6aa91627a7b1298a09025c136085f99ba31b1861f073a0"
        "696c4756cb156531ccf5c630154d66f3059b6b589617bd6bd711ef665079f879405"
    }
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


# We're kinda refactoring the stuff above to below
#
# The stuff above will become APIs to dashboards. The stuff below
# will register the actual dashboards.
COURSE_DASHBOARDS = [{
    'name': "Writing Observer",
    'url': "/static/repos/writing_observer/writing_observer/master/wobserver.html",
    "icon": {
        "type": "fas",
        "icon": "fa-pen-nib"
    }
}]

EXTRA_VIEWS = [{
    'name': 'NLP Options',
    'suburl': 'nlp-options',
    'static_json': INDICATOR_JSONS
}]
