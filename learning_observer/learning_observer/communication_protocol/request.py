'''
This file includes commands to create a request within the communication protocol.
'''
import enum

dispatch = "dispatch"
DISPATCH_MODES = enum.Enum('DISPATCH_MODES', 'PARAMETER VARIABLE CALL SELECT JOIN MAP')


def PARAMETER(parameter_name):
    """
    Returns a dictionary with the given parameter_name.

    :param parameter_name: the name of the parameter
    :type parameter_name: str
    :return: a dictionary containing the dispatch type and the parameter name
    :rtype: dict
    """
    return {
        dispatch: DISPATCH_MODES.PARAMETER,
        "parameter_name": parameter_name
    }


def VARIABLE(variable_name):
    """
    Returns a dictionary with the given variable_name.

    :param variable_name: the name of the variable
    :type variable_name: str
    :return: a dictionary containing the dispatch type and the variable name
    :rtype: dict
    """
    return {
        dispatch: DISPATCH_MODES.VARIABLE,
        "variable_name": variable_name
    }


def CALL(function_name):
    """
    Returns a callable that, when invoked, returns a dictionary containing the dispatch type, function name, arguments, and keyword arguments.

    :param function_name: the name of the function to call
    :type function_name: str
    :return: a callable object
    """
    def caller(*args, **kwargs):
        return {
            dispatch: DISPATCH_MODES.CALL,
            "function_name": function_name,
            "args": args,
            "kwargs": kwargs
        }
    setattr(caller, "__lo_name__", function_name)
    return caller


course_roster = CALL('learning_observer.course_roster')
latest_doc = CALL('writing_observer.latest_doc')  # <-- This should not be a call but a direct query into the KVS


def SELECT(keys):
    """
    Returns a dictionary with the given keys.

    :param keys: the keys to select
    :type keys: list
    :return: a dictionary containing the dispatch type and the keys
    :rtype: dict
    """
    return {
        dispatch: DISPATCH_MODES.SELECT,
        "keys": keys
    }


def JOIN(LEFT, RIGHT, LEFT_KEY, RIGHT_KEY):
    """
    Returns a dictionary representing a JOIN operation between LEFT and RIGHT based on LEFT_KEY and RIGHT_KEY.

    :param LEFT: the left table
    :type LEFT: dict
    :param RIGHT: the right table
    :type RIGHT: dict
    :param LEFT_KEY: the key to join on from the left table
    :type LEFT_KEY: str
    :param RIGHT_KEY: the key to join on from the right table
    :type RIGHT_KEY: str
    :return: a dictionary containing the dispatch type and the join information
    :rtype: dict
    """
    return {
        dispatch: DISPATCH_MODES.JOIN,
        "left": LEFT,
        "right": RIGHT,
        "left_key": LEFT_KEY,
        "right_key": RIGHT_KEY
    }


def MAP(function, values):
    """
    Returns a dictionary representing a MAP operation for the given function and values.

    :param function: the function to map
    :type function: callable
    :param values: the values to map over
    :type values: list
    :return: a dictionary containing the dispatch type, the function name, and the values
    :rtype: dict
    """
    return {
        dispatch: DISPATCH_MODES.MAP,
        "function": function.__lo_name__,
        "values": values
    }


def some_way_to_make_keys(text, doc_ids):
    """
    Some way to make keys. This is a placeholder function and needs to be implemented.
    
    :param text: text to generate keys from
    :type text: str
    :param doc_ids: document IDs to generate keys from
    :type doc_ids: list
    :return: a dictionary representing the keys
    :rtype: dict
    """
    # learning_observer.stream_analytics.helpers.make_key
    return {
        "dispatch": "keys",
        "doc_ids": doc_ids
    }


def MAKE_KEY(student_id):
    """
    Makes key based on student_id. This is a placeholder function and needs to be implemented.

    :param student_id: the student ID to make the key from
    :type student_id: str
    :return: a key
    :rtype: str
    """
    # learning_observer.stream_analytics.helpers.make_key
    return ""


EXAMPLE = {
    "execution_dag": {
        "roster": course_roster(course=PARAMETER("course_id")),
        "doc_ids": MAP(latest_doc, VARIABLE("roster")),
        "docs": SELECT(some_way_to_make_keys("document-text", VARIABLE("doc_ids"))),
        "combined": JOIN(LEFT=VARIABLE("docs"), RIGHT=VARIABLE("roster"), LEFT_KEY=MAKE_KEY(student_id="student_id"), RIGHT_KEY=MAKE_KEY(student_id="student.student_id"))
    },
    "returns": ["combined"],
    "name": "docs-with-roster",
    "description": "Here's what I do",
    "parameters": "Here's what I get called with, together with description"
}
