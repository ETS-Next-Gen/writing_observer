'''
Define layout for dashboard that allows teachers to interface
student essays with LLMs.
'''
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State

prefix = 'bulk-essay-analysis'
websocket = f'{prefix}-websocket'
ws_store = f'{prefix}-ws-store'

query_input = f'{prefix}-query-input'

advanced_collapse = f'{prefix}-advanced-collapse'
system_input = f'{prefix}-system-input'
rubric_upload = f'{prefix}-rubric-upload'
rubric_filename = f'{prefix}-rubric-filename'
rubric_store = f'{prefix}-rubric-store'

history_collapse = f'{prefix}-history-collapse'
history_store = f'{prefix}-history-store'

submit = f'{prefix}-submit-btn'
grid = f'{prefix}-essay-grid'

system_prompt = 'You are an assistant to a language arts teacher in a school setting. '\
    'Your task is to help the teacher assess, understand, and provide feedback on student essays.'


def layout():
    '''
    Generic layout function to create dashboard
    '''
    advanced = dbc.Col([
        lodrc.LOCollapse([
            dbc.InputGroup([
                dbc.InputGroupText('System prompt:'),
                dbc.Textarea(id=system_input, value=system_prompt, style={'height': '125px'})
            ]),
            dcc.Upload(
                html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files'),
                    html.Span(id=rubric_filename, className='ms-1')
                ]),
                id=rubric_upload,
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                },
                className_active='border-success',
                className_reject='border-danger',
                accept='.pdf'
            ),
            dcc.Store(id=rubric_store, data='')
        ], label='Advanced', id=advanced_collapse, is_open=False),
    ], width=6)

    history = dbc.Col([
        lodrc.LOCollapse([], id=history_collapse, is_open=False, label='History'),
        dcc.Store(id=history_store, data=[])
    ], width=6)

    cont = dbc.Container([
        html.H2('Prototype: Work in Progress'),
        html.P(
            'This dashboard is a prototype allowing teachers to run ChatGPT over a set of essays. '
            'The dashboard is subject to change based on ongoing feedback from teachers.'
        ),
        html.H2('Bulk Essay Analysis'),
        dbc.InputGroup([
            dbc.Textarea(id=query_input, placeholder='Type request here...', autofocus=True, value=''),
            dbc.Button('Submit', id=submit, n_clicks=0, disabled=True),
        ]),
        dbc.Row([advanced, history]),
        dbc.Row(id=grid, class_name='g-2 mt-2'),
        lodrc.LOConnection(id=websocket),
        dcc.Store(id=ws_store, data={})
    ], fluid=True)
    return dcc.Loading(cont)


# send request to LOConnection
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='send_to_loconnection'),
    Output(websocket, 'send'),
    Input(websocket, 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(submit, 'n_clicks'),
    State(query_input, 'value'),
    State(system_input, 'value'),
    State(rubric_store, 'data')
)

clientside_callback(
    '''function (value) {
        if (value.length === 0) { return true }
        return false
    }
    ''',
    Output(submit, 'disabled'),
    Input(query_input, 'value')
)

clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_input_history_on_query_submission'),
    Output(query_input, 'value'),
    Output(history_store, 'data'),
    Input(submit, 'n_clicks'),
    State(query_input, 'value'),
    State(history_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_history_list'),
    Output(history_collapse, 'children'),
    Input(history_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_rubric'),
    Output(rubric_store, 'data'),
    Output(rubric_filename, 'children'),
    Input(rubric_upload, 'contents'),
    Input(rubric_upload, 'filename')
)

# store message from LOConnection in storage for later use
clientside_callback(
    '''
    function(message) {
        const data = JSON.parse(message.data).wo.gpt_bulk
        return data
    }
    ''',
    Output(ws_store, 'data'),
    Input(websocket, 'message')
)

clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_student_grid'),
    Output(grid, 'children'),
    Input(ws_store, 'data'),
    Input(history_store, 'data')
)
