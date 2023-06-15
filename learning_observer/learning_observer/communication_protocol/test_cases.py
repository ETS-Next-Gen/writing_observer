"""
Run all test cases. Print output from the ones specified.

Usage:
    test_cases.py [<test_case>...]

Options:
    -h --help     Show this screen.

Test Cases:
    docs          Prints the dummy Google Docs text DAG.
    parameter     Prints the parameter test case.
    field         Prints the missing fields test case.
    malformed_key Prints the malformed key test case.
    func_except   Prints the func_except test case.
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
exception_func = q.call('learning_observer.dummycall')
map_func = q.call('learning_observer.dummymap')

DOCS_WITH_ROSTER_DAG = {
    "roster": course_roster(course=q.parameter("course_id")),
    "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
    "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
    "combined": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='context.context.STUDENT.value.user_id', RIGHT_ON='user_id')
}

DOCS_WITH_ROSTER_EXAMPLE = {
    "execution_dag": DOCS_WITH_ROSTER_DAG,
    "returns": ["combined"],
    "name": "docs-with-roster",
    "description": "Example of fetching students text information based on their last document.",
    "test_parameters": {"course_id": 123}
}
PARAMETER_ERROR_EXAMPLE = {
    "execution_dag": DOCS_WITH_ROSTER_DAG,
    "returns": ["combined"],
    "name": "parameter-error-example",
    "description": "Fetches student doc text; however, this errors since we do not provide the necessary parameters.",
    "test_parameters": {}
}
FIELD_ERROR_EXAMPLE = {
    "execution_dag": {
        "roster": course_roster(course=q.parameter("course_id")),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'nonexistent_key': 'doc_id'}),
    },
    "returns": ["doc_ids"],
    "name": "field-error-example",
    "description": "The desired field does not exist within our key. We output an error, but do no fail.",
    "test_parameters": {"course_id": 123}
}
MALFORMED_KEY_EXAMPLE = {
    "execution_dag": {
        "doc_ids": q.select([{'item': 1}, {'item': 2}], fields={'nonexistent_key': 'doc_id'}),
    },
    "returns": ["doc_ids"],
    "name": "malformed-key-error-example",
    "description": "Malformed key when trying to select",
    "test_parameters": {}
}
CALL_EXCEPTION_EXAMPLE = {
    "execution_dag": {
        "dummy": exception_func()
    },
    "returns": ["dummy"],
    "name": "call-exception-example",
    "description": "Throw exception within a published function",
    "test_parameters": {}
}
MAP_EXAMPLE = {
    'execution_dag': {
        'roster': course_roster(course=q.parameter("course_id")),
        'dummy': q.map(map_func, q.variable('roster'), 'user_id', {'example': 123})
    },
    "returns": ["dummy"],
    "name": "call-exception-example",
    "description": "Throw exception within a published function",
    "test_parameters": {'course_id': 123}
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


def raises_exception():
    raise Exception('This is an exception that was raised in a published function.')


async def dummy_map(value, example):
    if value.endswith('2'):
        raise ValueError('Item ends with a 2')
    return {'value': value, 'example': example}


def run_test_cases(test_cases):
    """
    Run all test cases. Print output from the ones specified.

    Args:
        test_cases (list): The test cases to be run

    Returns:
        None
    """
    # List of available test cases
    available_test_cases = ['docs', 'parameter', 'field', 'malformed_key', 'func_except', 'circular', 'dummy_map', 'all', 'none']

    if not all(case in available_test_cases for case in test_cases):
        print(f"Invalid test case. Available test cases are: {available_test_cases}")
        sys.exit()

    functions = {
        "learning_observer.dummyroster": dummy_roster,
        "learning_observer.dummycall": raises_exception,
        "learning_observer.dummymap": dummy_map
    }

    # Include the test_dags definition here
    test_dags = {
        'docs': DOCS_WITH_ROSTER_EXAMPLE,
        'parameter': PARAMETER_ERROR_EXAMPLE,
        'field': FIELD_ERROR_EXAMPLE,
        'malformed_key': MALFORMED_KEY_EXAMPLE,
        'func_except': CALL_EXCEPTION_EXAMPLE,
        'dummy_map': MAP_EXAMPLE
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
