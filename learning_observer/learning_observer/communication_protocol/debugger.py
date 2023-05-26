from dash import html, dcc, callback, Output, Input, State
from dash.exceptions import PreventUpdate
from dash_renderjson import DashRenderjson
import dash_bootstrap_components as dbc
import json
import lo_dash_react_components as lodrc


prefix = 'communication-debugger'
ws = f'{prefix}-websocket'
status = f'{prefix}-connection-status'
message = f'{prefix}-message-input'
submit = f'{prefix}-submit-btn'
response = f'{prefix}-response-markdown'


def layout():
    cont = dbc.Container(
        [
            dbc.Row(
                [
                    html.H1('Communication Protocol Debugger'),
                    lodrc.LOConnection(
                        id=ws,
                        url='ws://localhost:8888/wsapi/communication_dashboard'
                    ),
                    html.Div(id=status)
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2('Query'),
                            dbc.Textarea(
                                id=message,
                                placeholder='Input valid query',
                                value='{"output":{"function_name":"writing_observer.docs_with_roster","kwargs":{"course_id":123}}}',
                            ),
                            dbc.Button(
                                'Submit',
                                id=submit
                            )
                        ],
                        lg=6
                    ),
                    dbc.Col(
                        [
                            html.H2('Response'),
                            DashRenderjson(
                                id=response,
                                invert_theme=True,
                                max_depth=4
                            )
                        ],
                        lg=6
                    )
                ],
            )
        ],
        fluid=True
    )
    return cont


def create_status(title, icon):
    return html.Div(
        [
            html.I(className=f'{icon} me-1'),
            title
        ]
    )


@callback(
    Output(status, 'children'),
    Input(ws, 'state')
)
def update_status(state):
    icons = ['fas fa-sync-alt', 'fas fa-check text-success', 'fas fa-sync-alt', 'fas fa-times text-danger']
    titles = ['Connecting to server', 'Connected to server', 'Closing connection', 'Disconnected from server']
    index = state.get('readyState', 3) if state is not None else 3
    return create_status(titles[index], icons[index])


@callback(
    Output(submit, 'disabled'),
    Input(message, 'value')
)
def determine_valid_json(value):
    if value is None:
        return True
    try:
        json.loads(value)
        return False
    except ValueError:
        return True


@callback(
    Output(ws, 'send'),
    Input(submit, 'n_clicks'),
    State(message, 'value')
)
def send_message(clicks, value):
    if clicks is None:
        raise PreventUpdate
    return value


@callback(
    Output(response, 'data'),
    Input(ws, 'message')
)
def receive_message(message):
    if message is None:
        return {}
    return json.loads(message.get("data", {}))
