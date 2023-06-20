"""
Run all test cases. Print output from the ones specified.

Usage:
    test_cases.py [<test_case>...]

Options:
    -h --help     Show this screen.

Test Cases:
    docs_with_roster    Prints the dummy Google Docs text DAG.
    map_example         Prints the map example test cases.
    parameter_error     Prints the parameter test case.
    field_error         Prints the missing fields test case.
    malformed_key       Prints the malformed key test case.
    call_exception      Prints the func_except test case.
    all                 Prints all available test cases.
    none                Prints no output, except on unexpected errors
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


# dummy functions for testing
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


def dummy_exception():
    raise Exception('This is an exception that was raised in a published function.')


async def dummy_map(value, example):
    if value.endswith('2'):
        raise ValueError('Item ends with a 2')
    return {'value': value, 'example': example}


DUMMY_FUNCTIONS = {
    "learning_observer.dummyroster": dummy_roster,
    "learning_observer.dummycall": dummy_exception,
    "learning_observer.dummymap": dummy_map
}

course_roster = q.call('learning_observer.dummyroster')
exception_func = q.call('learning_observer.dummycall')
map_func = q.call('learning_observer.dummymap')

TEST_DAG = {
    'execution_dag': {
        "roster": course_roster(course=q.parameter("course_id")),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
        "docs_join_roster": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='context.context.STUDENT.value.user_id', RIGHT_ON='user_id'),
        "map_students": q.map(map_func, q.variable('roster'), 'user_id', {'example': 123}),
        "field_error": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'nonexistent_key': 'doc_id'}),
        "malformed_key_error": q.select([{'item': 1}, {'item': 2}], fields={'nonexistent_key': 'doc_id'}),
        "call_exception": exception_func()
    },
    'exports': {
        'docs_with_roster': {
            'returns': 'docs_join_roster',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": "Example of fetching students text information based on their last document.",
        },
        'map_example': {
            'returns': 'map_students',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": 'Show example of mapping students'
        },
        'parameter_error': {
            'returns': 'docs_join_roster',
            'parameters': ['course_id'],
            'test_parameters': {},
            "description": "Fetches student doc text; however, this errors since we do not provide the necessary parameters.",
        },
        'field_error': {
            'returns': 'field_error',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": "The desired field does not exist within our key. We output an error, but do no fail.",
        },
        'malformed_key': {
            'returns': 'malformed_key_error',
            'parameters': [],
            'test_parameters': {},
            "description": "Malformed key when trying to select",
        },
        'call_exception': {
            'returns': 'call_exception',
            'parameters': [],
            'test_parameters': {},
            'description': "Throw an exception within a published function"
        }
    },
    'parameters': [
        {
            'id': 'course_id',
            'node': 'roster',
            'type': [str],
            'required': True,
            'description': 'the ID of the course in which we wish to receive data for'
        }
    ]
}


def run_test_cases(test_cases):
    """
    Run all test cases. Print output from the ones specified.

    Args:
        test_cases (list): The test cases to be run

    Returns:
        None
    """
    # List of available test cases
    available_test_cases = list(TEST_DAG['exports'].keys()) + ['all', 'none']

    if not all(case in available_test_cases for case in test_cases):
        print(f"Invalid test case. Available test cases are: {available_test_cases}")
        sys.exit()

    learning_observer.offline.init()

    for key in TEST_DAG['exports']:
        FLAT = learning_observer.communication_protocol.util.flatten(copy.deepcopy(TEST_DAG))
        EXECUTE = asyncio.run(
            learning_observer.communication_protocol.executor.execute_dag(
                copy.deepcopy(FLAT), parameters=TEST_DAG['exports'][key]['test_parameters'],
                functions=DUMMY_FUNCTIONS, target_exports=[key]
            )
        )
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
