'''
This file will detail how to build a dashboard using
the Dash framework.

If you are unfamiliar with Dash, it compiles python code
to react and serves it via a Flask server. You can register
callbacks to run when specific states change. Normal callbacks
execute Python code server side, but Clientside callbacks
execute Javascript code client side. Clientside functions are
preferred as it cuts down server and network resources.
'''
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc


_prefix = {{ cookiecutter.project_prefix }}
_websocket = f'{_prefix}-websocket'
_websocket_storage = f'{_prefix}-websocket-store'
_output = f'{_prefix}-output'

def layout():
    '''
    Function to define the page's layout.
    '''
    page_layout = html.Div(children=[
        html.H1(children='Event counts'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionStatusAIO(aio_id=_websocket)),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ]),
        dcc.Store(id=_websocket_storage),
        html.Div(id=_output)
    ])
    return page_layout

# Send the initial state based on the url hash to LO.
# If this is not included, nothing will be returned from
# the communication protocol.
clientside_callback(
    ClientsideFunction(namespace='{{ cookiecutter.project_slug }}', function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash')
)

# Handle receiving a message from the websocket.
# This step will parse the message and update the
# local storage accordingly.
clientside_callback(
    ClientsideFunction(namespace='{{ cookiecutter.project_slug }}', function_name='receiveWSMessage'),
    Output(_websocket_storage, 'data'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'message'),
    prevent_initial_call=True
)

# Build the UI based on what we've received from the
# communicaton protocol
# This clientside callback and the serverside callback below are
# the same
# clientside_callback(
#     ClientsideFunction(namespace='{{ cookiecutter.project_slug }}', function_name='populateOutput'),
#     Output(_output, 'children'),
#     Input(_websocket_storage, 'data'),
# )


@callback(
    Output(_output, 'children'),
    Input(_websocket_storage, 'data'),
)
def populate_output(data):
    if not data:
        return 'No students'
    output = [html.Div([
        lodrc.LONameTag(
            profile=s['profile'], className='d-inline-block student-name-tag',
            includeName=True, id=f'{s["user_id"]}-name-tag'
        ),
        html.Span(f' - {s["count"]} events')
    ]) for s in data]
    return output
