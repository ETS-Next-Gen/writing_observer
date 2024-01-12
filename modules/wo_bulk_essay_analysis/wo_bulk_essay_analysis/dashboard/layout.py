'''
Define layout for dashboard that allows teachers to interface
student essays with LLMs.
'''
import dash_bootstrap_components as dbc
from dash_renderjson import DashRenderjson
import datetime
import lo_dash_react_components as lodrc

from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL

# TODO pull this flag from settings
DEBUG_FLAG = True

prefix = 'bulk-essay-analysis'
websocket = f'{prefix}-websocket'
ws_store = f'{prefix}-ws-store'
error_store = f'{prefix}-error-store'

alert = f'{prefix}-alert'
alert_text = f'{prefix}-alert-text'
alert_error_dump = f'{prefix}-alert-error-dump'

query_input = f'{prefix}-query-input'

panel_layout = f'{prefix}-panel-layout'

advanced_collapse = f'{prefix}-advanced-collapse'
system_input = f'{prefix}-system-prompt-input'
# document source
doc_src = f'{prefix}-doc-src'
doc_src_date = f'{prefix}-doc-src-date'
doc_src_timestamp = f'{prefix}-doc-src-timestamp'

attachment_upload = f'{prefix}-attachment-upload'
attachment_label = f'{prefix}-attachment-label'
attachment_extracted_text = f'{prefix}-attachment-extracted-text'
attachment_save = f'{prefix}-attachment-save'
attachment_warning_message = f'{prefix}-attachment-warning-message'
attachment_store = f'{prefix}-attachment-store'

tags = f'{prefix}-tags'
tag = f'{prefix}-tag'
tag_store = f'{prefix}-tags-store'

history_body = f'{prefix}-history-body'
history_store = f'{prefix}-history-store'
favorite_store = f'{prefix}-favorite-store'

submit = f'{prefix}-submit-btn'
submit_warning_message = f'{prefix}-submit-warning-msg'
grid = f'{prefix}-essay-grid'

# default prompts
system_prompt = 'You are an assistant to a language arts teacher in a school setting. '\
    'Your task is to help the teacher assess, understand, and provide feedback on student essays.'

starting_prompt = 'Provide 3 bullet points summarizing the following text:\n{student_text}'


def layout():
    '''
    Generic layout function to create dashboard
    '''
    # advanced menu for system prompt
    advanced = dbc.Col([
        lodrc.LOCollapse([
            dbc.InputGroup([
                dbc.InputGroupText('System prompt:'),
                dbc.Textarea(id=system_input, value=system_prompt)
            ]),
            html.Div([
                dbc.Label('Document Source'),
                dbc.RadioItems(options=[
                    {'label': 'Latest Document', 'value': 'latest' },
                    {'label': 'Specific Time', 'value': 'ts'},
                ], value='latest', id=doc_src),
                dbc.InputGroup([
                    dcc.DatePickerSingle(id=doc_src_date, date=datetime.date.today()),
                    dbc.Input(type='time', id=doc_src_timestamp, value=datetime.datetime.now().strftime("%H:%M"))
                ])
            ])
        ], label='Advanced', id=advanced_collapse, is_open=False),
    ])

    # history panel
    history_favorite_panel = dbc.Card([
        dbc.CardHeader('Prompts'),
        dbc.CardBody([], id=history_body),
        dcc.Store(id=history_store, data=[])
    ], class_name='h-100')

    # attachment information panel
    attachment_panel = dbc.Card([
        dbc.CardHeader('Upload'),
        dbc.CardBody([
            dbc.Label('What is this?'),
            dbc.Input(placeholder='e.g. argumentative attachment', id=attachment_label, value=''),
            dbc.Label('Extracted text from attachment'),
            dbc.Textarea(value='', id=attachment_extracted_text, style={'height': '300px'})
        ]),
        dbc.CardFooter([
            html.Small(id=attachment_warning_message, className='text-danger'),
            dbc.Button('Save', id=attachment_save, color='primary', n_clicks=0, class_name='float-end')
        ]),
        dcc.Store(id=attachment_store, data='')
    ], class_name='h-100')

    # query creator panel
    input_panel = dbc.Card([
        dbc.InputGroup([
            dbc.InputGroupText([], id=tags, class_name='flex-grow-1', style={'gap': '5px'}),
            dcc.Store(id=tag_store, data={'student_text': ''}),
            dbc.Button(dcc.Upload([html.I(className='fas fa-plus me-1'), 'Upload'], accept='.pdf', id=attachment_upload))
        ]),
        dbc.CardBody(dbc.Textarea(id=query_input, value=starting_prompt, class_name='h-100', style={'minHeight': '150px'})),
        dbc.CardFooter([
            html.Small(id=submit_warning_message, className='text-danger'),
            dbc.Button('Submit', color='primary', id=submit, n_clicks=0, class_name='float-end')
        ])
    ], class_name='h-100')

    alert_component = dbc.Alert([
        html.Div(id=alert_text),
        html.Div(DashRenderjson(id=alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
    ], id=alert, color='danger', is_open=False)

    # overall container
    cont = dbc.Container([
        html.H2('Prototype: Work in Progress'),
        html.P(
            'This dashboard is a prototype allowing teachers to run ChatGPT over a set of essays. '
            'The dashboard is subject to change based on ongoing feedback from teachers.'
        ),
        html.H2('AskGPT'),
        lodrc.LOPanelLayout(
            input_panel,
            panels=[
                {'children': history_favorite_panel, 'width': '20%', 'id': 'history-favorite', 'side': 'left'},
                {'children': attachment_panel, 'width': '40%', 'id': 'attachment'},
            ],
            shown=['history-favorite'],
            id=panel_layout
        ),
        dbc.Row([advanced]),
        alert_component,
        dbc.Row(id=grid, class_name='g-2 mt-2'),
        lodrc.LOConnection(id=websocket),
        dcc.Store(id=ws_store, data=[]),
        dcc.Store(id=error_store, data=False)
    ], fluid=True)
    return dcc.Loading(cont)


# disbale document date/time options
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disable_doc_src_datetime'),
    Output(doc_src_date, 'disabled'),
    Output(doc_src_timestamp, 'disabled'),
    Input(doc_src, 'value')
)

# send request on websocket
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='send_to_loconnection'),
    Output(websocket, 'send'),
    Input(websocket, 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(submit, 'n_clicks'),
    Input(doc_src, 'value'),
    Input(doc_src_date, 'date'),
    Input(doc_src_timestamp, 'value'),
    State(query_input, 'value'),
    State(system_input, 'value'),
    State(tag_store, 'data'),
)

# enable/disabled submit based on query
# makes sure there is a query and the tags are properly formatted
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='disabled_query_submit'),
    Output(submit, 'disabled'),
    Output(submit_warning_message, 'children'),
    Input(query_input, 'value'),
    State(tag_store, 'data')
)

# add submitted query to history and clear input
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_input_history_on_query_submission'),
    Output(query_input, 'value'),
    Output(history_store, 'data'),
    Input(submit, 'n_clicks'),
    State(query_input, 'value'),
    State(history_store, 'data')
)

# update history based on history browser storage
# TODO create a history component that can handle favorites
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_history_list'),
    Output(history_body, 'children'),
    Input(history_store, 'data')
)

# show attachment panel upon uploading document and populate fields
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='open_and_populate_attachment_panel'),
    Output(attachment_extracted_text, 'value'),
    Output(attachment_label, 'value'),
    Output(panel_layout, 'shown'),
    Input(attachment_upload, 'contents'),
    Input(attachment_upload, 'filename'),
    Input(attachment_upload, 'last_modified'),
    State(panel_layout, 'shown')
)

# store message from LOConnection in storage for later use
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='receive_ws_message'),
    Output(ws_store, 'data'),
    Output(error_store, 'data'),
    Input(websocket, 'message'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_alert_with_error'),
    Output(alert_text, 'children'),
    Output(alert, 'is_open'),
    Output(alert_error_dump, 'data'),
    Input(error_store, 'data')
)

# update student cards based on new data in storage
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_student_grid'),
    Output(grid, 'children'),
    Input(ws_store, 'data'),
    Input(history_store, 'data')
)

# append tag in curly braces to input
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='add_tag_to_input'),
    Output(query_input, 'value', allow_duplicate=True),
    Input({'type': tag, 'index': ALL}, 'n_clicks'),
    State(query_input, 'value'),
    State(tag_store, 'data'),
    prevent_initial_call=True
)

# enable/disable the save attachment button if tag is already in use/blank
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='disable_attachment_save_button'),
    Output(attachment_save, 'disabled'),
    Output(attachment_warning_message, 'children'),
    Input(attachment_label, 'value'),
    State({'type': tag, 'index': ALL}, 'value')
)

# populate word bank of tags
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_tag_buttons'),
    Output(tags, 'children'),
    Input(tag_store, 'data')
)

# save attachment to tag storage
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='save_attachment'),
    Output(tag_store, 'data'),
    Output(panel_layout, 'shown', allow_duplicate=True),
    Input(attachment_save, 'n_clicks'),
    State(attachment_label, 'value'),
    State(attachment_extracted_text, 'value'),
    State(tag_store, 'data'),
    State(panel_layout, 'shown'),
    prevent_initial_call=True
)
