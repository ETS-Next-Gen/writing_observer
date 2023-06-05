"""
Run all test cases. Print output from the ones specified.

Usage:
    test_cases.py [<test_case>...]

Options:
    -h --help     Show this screen.

Test Cases:
    docs          Prints the dummy Google Docs text DAG.
    exception     Prints the exception test cases.
    circular      Prints the circular reference test cases.
    all           Prints all available test cases.
    none          Prints no output, except on unexpected errors
"""

import argparse
import asyncio
import collections
import copy
import docopt
import json
import sys

import learning_observer.communication_protocol.query as q
import learning_observer.communication_protocol.util
import learning_observer.communication_protocol.executor
import learning_observer.offline

args = docopt.docopt(__doc__)
if args['<test_case>'] == []:
    print(__doc__)
    sys.exit()

# TODO: Validate that the test cases are valid


def dummy_roster(course):
    """
    Dummy function for course roster.

    :param course: The course identifier
    :type course: str
    :return: A list of student identifiers
    :rtype: list
    """
    return [{
        'user_id': f'student-{i}'
    } for i in range(10)]


functions = {
    "learning_observer.course_roster": dummy_roster
}

course_roster = q.call('learning_observer.course_roster')

DOCS_WITH_ROSTER_EXAMPLE = {
    "execution_dag": {
        "roster": course_roster(course=q.parameter("course_id")),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'some_key.nested': 'doc_id'}),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'some_key.nested': 'text'}),
        "combined": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='context.context.STUDENT.value.user_id', RIGHT_ON='user_id')
    },
    "returns": ["combined"],
    "name": "docs-with-roster",
    "description": "Here's what I do",
    "parameters": "Here's what I get called with, together with description"
}
EXCEPTION_EXAMPLE = {}
ACCIDENTALLY_CIRCULAR_DAG_EXAMPLE = {}
# ... and so on

# TODO: Consider DRY with docstring and this dictionary
test_dags = {
    'docs': DOCS_WITH_ROSTER_EXAMPLE
}

learning_observer.offline.init()

for key in test_dags:
    FLAT = learning_observer.communication_protocol.util.flatten(copy.deepcopy(test_dags[key]))
    EXECUTE = asyncio.run(learning_observer.communication_protocol.executor.execute_dag(copy.deepcopy(FLAT), parameters={"course_id": 12345}, functions=functions))
    if key in args['<test_case>']:
        print("Execute:", json.dumps(EXECUTE, indent=2))
