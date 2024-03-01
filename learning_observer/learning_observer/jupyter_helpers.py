from aiohttp import web
import asyncio
import IPython.display
import ipywidgets

import learning_observer.communication_protocol.query as q
import learning_observer.dashboard
import learning_observer.module_loader
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
        'context': f'{module}.{id}',
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


async def serve_communication_protocol_endpoint(port=8765):
    '''Run simple aiohttp webserver to connect with communication protocol
    This code will throw an error that the port is already in use
    The server will not currently stop properly if connections are
    stilll active.
    TODO figure out a better way to start/stop this
    '''
    app = web.Application()
    # users need teacher access to see this websocket method
    # set the `auth.test_case_insecure` in `creds.yaml` to True
    # to bypass this check
    app.router.add_route('GET', '/ws', learning_observer.dashboard.websocket_dashboard_handler)

    # Using an `AppRunner` (as opposed to `run_app`) will connect
    # to the existing ipython kernel loop to serve the websocket.
    runner = web.AppRunner(app, tcp_keepalive=False)
    async def start_server():
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        print('Started server')
        await site.start()
        print('Started server')

    async def stop_server():
        await runner.cleanup()
        print('Server stopped')

    start_button = ipywidgets.Button(description="Start Server")
    stop_button = ipywidgets.Button(description="Stop Server", disabled=True)  # Initially disabled

    async def start_server_wrapper():
        await start_server()
        # Disable start button and enable stop button upon server start
        start_button.disabled = True
        stop_button.disabled = False

    async def stop_server_wrapper():
        await stop_server()
        # Disable stop button and enable start button upon server stop
        stop_button.disabled = True
        start_button.disabled = False

    def on_start_clicked(b):
        asyncio.create_task(start_server_wrapper())

    def on_stop_clicked(b):
        asyncio.create_task(stop_server_wrapper())

    start_button.on_click(on_start_clicked)
    stop_button.on_click(on_stop_clicked)

    IPython.display.display(start_button, stop_button)
