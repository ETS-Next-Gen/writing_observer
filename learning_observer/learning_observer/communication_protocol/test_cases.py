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

import asyncio
import copy
import docopt
import json
import sys

import learning_observer.communication_protocol.executor
import learning_observer.communication_protocol.integration
import learning_observer.communication_protocol.query as q
import learning_observer.communication_protocol.util
import learning_observer.offline

# TODO: Validate that the test cases are valid
course_roster = q.call('learning_observer.dummyroster')

DOCS_WITH_ROSTER_EXAMPLE = {
    "execution_dag": {
        "roster": course_roster(course=q.parameter("course_id")),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'some_key.nested': 'doc_id'}),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'some_key.nested': 'text'}),
        "combined": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='context.context.STUDENT.value.user_id', RIGHT_ON='user_id')
    },
    "returns": ["combined"],
    "name": "docs-with-roster",
    "description": "Example of fetching students text information based on their last document.",
    "test_parameters": {"course_id": 123}
}
EXCEPTION_EXAMPLE = {
    "execution_dag": {
        "roster": course_roster(course=q.parameter("course_id")),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'some_key.nested': 'doc_id'}),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'some_key.nested': 'text'}),
        "combined": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='context.context.STUDENT.value.user_id', RIGHT_ON='user_id')
    },
    "returns": ["combined"],
    "name": "exception-example",
    "description": "Fetches student doc text; however, this errors since we do not provide the necessary parameters.",
    "test_parameters": {}
}
# TODO make this a circular example for real
ACCIDENTALLY_CIRCULAR_DAG_EXAMPLE = {}


def dummy_roster(course):
    """
    Dummy function for course roster.

    Args:
        course: The course identifier

    Returns:
        list: A list of student identifiers
    """
    return [{
        'user_id': f'student-{i}'
    } for i in range(10)]


def run_test_cases(test_cases):
    """
    Run all test cases. Print output from the ones specified.

    Args:
        test_cases (list): The test cases to be run

    Returns:
        None
    """
    # List of available test cases
    available_test_cases = ['docs', 'exception', 'circular', 'all', 'none']

    if not all(case in available_test_cases for case in test_cases):
        print(f"Invalid test case. Available test cases are: {available_test_cases}")
        sys.exit()

    functions = {"learning_observer.dummyroster": dummy_roster}

    # Include the test_dags definition here
    test_dags = {
        'docs': DOCS_WITH_ROSTER_EXAMPLE,
        'exception': EXCEPTION_EXAMPLE,
        # additional test cases...
    }

    learning_observer.offline.init()

    for key in test_dags:
        FLAT = learning_observer.communication_protocol.util.flatten(copy.deepcopy(test_dags[key]))
        EXECUTE = asyncio.run(learning_observer.communication_protocol.executor.execute_dag(copy.deepcopy(FLAT), parameters=test_dags[key]['test_parameters'], functions=functions))
        if (key in test_cases or 'all' in test_cases) and 'none' not in test_cases:
            print(f"Execute {key}:", json.dumps(EXECUTE, indent=2))


if __name__ == "__main__":
    """
    Program entry point
    """
    args = docopt.docopt(__doc__)
    if args['<test_case>'] == []:
        print(__doc__)
        sys.exit()
    run_test_cases(args['<test_case>'])
