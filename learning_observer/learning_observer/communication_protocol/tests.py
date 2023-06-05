import collections
import copy
import json

import learning_observer.communication_protocol.query
import learning_observer.offline
from learning_observer.communication_protocol.executor import flatten, execute_dag

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

# Setup KVS since LO.KVS() isn't available here

def create_kvs():
    async def return_value():
        return {'some_key': {'nested': 'some_key_value'}}
    return collections.defaultdict(return_value)
KVS = create_kvs

functions = {
    "learning_observer.course_roster": dummy_roster
}

learning_observer.offline.init()

# print("Source:", json.dumps(learning_observer.communication_protocol.query.EXAMPLE, indent=2))
FLAT = flatten(copy.deepcopy(learning_observer.communication_protocol.query.EXAMPLE))
# print("Flat:", json.dumps(FLAT, indent=2))
import asyncio
EXECUTE = asyncio.run(execute_dag(copy.deepcopy(FLAT), parameters={"course_id": 12345}, functions=functions))
print("Execute:", json.dumps(EXECUTE, indent=2))
