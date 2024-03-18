import learning_observer.communication_protocol.query as q
import learning_observer.dashboard
import learning_observer.kvs
import learning_observer.module_loader
import learning_observer.stream_analytics
from learning_observer.stream_analytics.helpers import KeyField, Scope

MODULE_NAME = 'jupyter-helper'

def _transform_reducer_into_classroom_query(id):
    '''Take a reducer and create the execution dag to run
    that query over a classroom.

    HACK much of this is hardcoded and needs to be abstracted

    This relies on the reducer having `scope=Scope([KeyField.STUDENT])`.
    '''
    course_roster = q.call('learning_observer.courseroster')
    # TODO replace event_count stuff with more general items
    dag = {
        "execution_dag": {
            "roster": course_roster(runtime=q.parameter("runtime"), course_id=q.parameter("course_id", required=True)),
            'event_count': q.select(q.keys(id, STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'event_count': 'event_count'}),
        },
        "exports": {
            'event_count': {
                'returns': 'event_count',
                'parameters': ['course_id']
            }
        }
    }
    return dag


async def remove_reducer_results_from_kvs(reducer_id):
    '''Find all keys that match the reducer and remove them
    '''
    kvs = learning_observer.kvs.KVS()
    keys = await kvs.keys()
    matched_keys = [k for k in keys if reducer_id in k]
    for m in matched_keys:
        await kvs.remove(m)
    return matched_keys


async def reload_reducer(
        reducer_id, reducer_func, module=MODULE_NAME,
        scope=None, default=None, create_new=False
    ):
    scope = scope if scope else Scope([KeyField.STUDENT])
    reducer = {
        # TODO not sure the best way to handle specifying context
        # 'context': f'{module}.{id}',
        'context': 'org.mitros.writing_analytics',
        'function': reducer_func,
        'scope': scope,
        'default': default,
        'module': module,
        'id': reducer_id
    }

    reducers = learning_observer.module_loader.reducers()
    existing_reducer = any(r['id'] == reducer_id for r in reducers)
    if not existing_reducer and not create_new:
        error_msg = f'The reducer, `{reducer_id}`, does not currently '\
            'exist and the `create_new` parameter is set to False. '\
            'To create the reducer if its missing use:\n'\
            '`reload_reducer(..., create_new=True)`'
        raise RuntimeError(error_msg)

    removed_keys = []
    if existing_reducer:
        # remove existing reducer from running reducers
        # and then clear all data associated with that reducer
        learning_observer.module_loader.remove_reducer(reducer_id)
        learning_observer.stream_analytics.init()
        removed_keys = await remove_reducer_results_from_kvs(reducer_id)

    # TODO process reducer over files corresponding to the removed keys
    # files_to process = find_files(removed_keys)
    # await learning_observer.offline.process_files(files_to_process)

    learning_observer.module_loader.add_reducer(reducer)
    learning_observer.stream_analytics.init()

    return
    # TODO update the execution dag
    # create a simple "module" to set the execution dag
    obj = lambda: None
    obj.EXECUTION_DAG = _transform_reducer_into_classroom_query(id)
    learning_observer.module_loader.load_execution_dags(module, obj)

# TODO: Next steps:
#
# * What happens when we load a reducer and want to replace it with a newer version?
# * How do we handle old data when we add a reducer?
# * How do we clear / handle obsolete data in the KVS from an old reducer?
#
# Get to where we can do iterative development
#
# This should be integrated with `offline.py`.
