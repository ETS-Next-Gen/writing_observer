'''
Define layout for dashboard that allows teachers to interface
student essays with LLMs.
'''
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

from dash import html, dcc, callback, Patch, clientside_callback, ClientsideFunction, Output, Input, State

prefix = 'bulk-essay-analysis'
websocket = f'{prefix}-websocket'
ws_store = f'{prefix}-ws-store'

query_input = f'{prefix}-query-input'
submit = f'{prefix}-submit-btn'
chat = f'{prefix}-chat-panel'
grid = f'{prefix}-essay-grid'

welcome_message = ['Hello, welcome to the bulk essay analysis.', 'Provide a prompt and we will pass it along with each text into ChatGPT.']


def layout():
    '''
    Generic layout function to create dashboard
    '''
    main = html.Div([
        html.H2('Bulk Essay Analysis'),
        dbc.Row(id=grid, class_name='g-2')
    ], className='vh-100', style={'overflowY': 'auto', 'overflowX': 'hidden'})
    starting_message = dbc.Col(
        dbc.Card(
            [html.P(message) for message in welcome_message],
            body=True,
            color='#fff'
        ),
        width=9,
        align='start'
    )
    chat_panel = dbc.Row([
        dbc.Col(
            dbc.Row([starting_message], id=chat, class_name='h-100 flex-column-reverse flex-nowrap overflow-auto g-1'),
            class_name='flex-grow-1 overflow-auto',
        ),
        dbc.Col(
            dbc.InputGroup([
                dbc.Textarea(id=query_input, placeholder='Type request here...', autofocus=True, value=''),
                dbc.Button('Submit', id=submit, n_clicks=0, disabled=True),
            ], class_name='p-1'),
            width=12,
            align='end'
        ),
    ], class_name='vh-100 flex-column')
    cont = dbc.Container([
        lodrc.LOPanelLayout(
            main,
            panels=[{'children': chat_panel, 'width': '25%', 'id': 'chat'}],
            shown=['chat']
        ),
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
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_ui_upon_query_submission'),
    Output(query_input, 'value'),
    Output(chat, 'children'),
    Input(submit, 'n_clicks'),
    State(query_input, 'value'),
    State(chat, 'children')
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
    Input(ws_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='add_response_to_chat'),
    Output(chat, 'children', allow_duplicate=True),
    Input(ws_store, 'data'),
    State(chat, 'children'),
    prevent_initial_call=True
)
