from aiohttp import web

import learning_observer.communication_protocol.query as q
import learning_observer.dashboard
import learning_observer.module_loader
from learning_observer.stream_analytics.helpers import KeyField, Scope

MODULE_NAME = 'jupyter-helper'

def _transform_reducer_into_classroom_query(id):
    '''Take a reducer and create the execution dag to run
    that query over a classroom.

    This relies on the reducer being built for student level.
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
    reducer = {
        'context': f'{module}.{id}',
        'function': reducer,
        'scope': Scope([KeyField.STUDENT]),
        'default': default,
        'module': module,
        'id': id
    }
    learning_observer.module_loader.add_reducer(reducer, id)
    obj = lambda: None
    obj.EXECUTION_DAG = _transform_reducer_into_classroom_query(id)
    learning_observer.module_loader.load_execution_dags(module, obj)


async def serve_communication_protocol_endpoint(port=8765):
    '''Run simple aiohttp webserver to connect with communication protocol
    This code will throw an error that the port is already in use
    TODO figure out a better way to start/stop this
    '''
    app = web.Application()
    # users need teacher access to see this websocket method
    # set the `auth.test_case_insecure` in `creds.yaml` to True
    # to bypass this check
    app.router.add_route('GET', '/ws', learning_observer.dashboard.websocket_dashboard_handler)

    # this is needed to start up the code from within
    # the jupyter lab/notebook (TODO test notebook)
    # TODO document why we need the apprunner over the app
    # Is this something we should thread here instead?
    # I was running into issues with stopping sometimes.
    runner = web.AppRunner(app)
    async def start_app():
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port, shutdown_timeout=600)
        await site.start()
    await start_app()

