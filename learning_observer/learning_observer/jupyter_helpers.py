import learning_observer.communication_protocol.query as q
import learning_observer.dashboard
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


def add_reducer_to_execution_dag(id, reducer, module=MODULE_NAME, default=None):
    '''Load `reducer` into LO's available execution DAGs. This allows us
    to query the reducer through the `dashboard.websocket_dashboard_handler`
    endpoint later on.
    '''
    reducer = {
        # TODO not sure the best way to handle specifying context
        # 'context': f'{module}.{id}',
        'context': 'org.mitros.writing_analytics',
        'function': reducer,
        'scope': Scope([KeyField.STUDENT]),
        'default': default,
        'module': module,
        'id': id
    }
    learning_observer.module_loader.add_reducer(reducer, id)
    # create a mocked module to set load execution dags
    obj = lambda: None
    obj.EXECUTION_DAG = _transform_reducer_into_classroom_query(id)
    learning_observer.module_loader.load_execution_dags(module, obj)
    learning_observer.stream_analytics.init()
