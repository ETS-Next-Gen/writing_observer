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
_websocket = f'{prefix}-websocket'
_namespace = 'bulk_essay_feedback'

alert = f'{prefix}-alert'
alert_text = f'{prefix}-alert-text'
alert_error_dump = f'{prefix}-alert-error-dump'

query_input = f'{prefix}-query-input'

panel_layout = f'{prefix}-panel-layout'

_advanced_toggle = f'{prefix}-advanced-toggle'
_advanced_collapse = f'{prefix}-advanced-collapse'

system_input = f'{prefix}-system-prompt-input'
# document source DOM ids
doc_src = f'{prefix}-doc-src'
doc_src_date = f'{prefix}-doc-src-date'
doc_src_timestamp = f'{prefix}-doc-src-timestamp'

# attachment upload DOM ids
attachment_upload = f'{prefix}-attachment-upload'
attachment_label = f'{prefix}-attachment-label'
attachment_extracted_text = f'{prefix}-attachment-extracted-text'
attachment_save = f'{prefix}-attachment-save'
attachment_warning_message = f'{prefix}-attachment-warning-message'
attachment_store = f'{prefix}-attachment-store'

# placeholder DOM ids
tags = f'{prefix}-tags'
placeholder_tooltip = f'{prefix}-placeholder-tooltip'
tag = f'{prefix}-tag'
tag_store = f'{prefix}-tags-store'

# prompt history DOM ids
history_body = f'{prefix}-history-body'
history_store = f'{prefix}-history-store'
favorite_store = f'{prefix}-favorite-store'

# loading message/bar DOM ids
_loading_prefix = f'{prefix}-loading'
_loading_collapse = f'{_loading_prefix}-collapse'
_loading_progress = f'{_loading_prefix}-progress-bar'
_loading_information = f'{_loading_prefix}-information-text'

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
    advanced = [
        html.Div([
            dbc.Label('System prompt'),
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
    ]

    # history panel
    history_favorite_panel = dbc.Card([
        dbc.CardHeader('Prompt History'),
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
        dbc.CardHeader('Prompt Input'),
        # TODO figure out the proper way to create new tags/upload docs
        # then remove the `class_name='d-none'` from this button.
        dbc.Button(dcc.Upload([html.I(className='fas fa-plus me-1'), 'Upload'], accept='.pdf', id=attachment_upload), class_name='d-none'),
        dbc.CardBody([
            dbc.Textarea(id=query_input, value=starting_prompt, class_name='h-100', style={'minHeight': '150px'}),
            html.Div([
                html.Span([
                    'Placeholders',
                    html.I(className='fas fa-circle-question ms-1', id=placeholder_tooltip)
                ], className='me-1'),
                html.Span([], id=tags),
            ], className='mt-1'),
            dbc.Tooltip(
                'Click a placeholder to insert it into your prompt. Upon submission, it will be replaced with the corresponding value.',
                target=placeholder_tooltip
            ),
            dcc.Store(id=tag_store, data={'student_text': ''}),
        ]),
        dbc.CardFooter([
            html.Small(id=submit_warning_message, className='text-danger'),
            dbc.Button('Submit', color='primary', id=submit, n_clicks=0, class_name='float-end')
        ])
    ])

    alert_component = dbc.Alert([
        html.Div(id=alert_text),
        html.Div(DashRenderjson(id=alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
    ], id=alert, color='danger', is_open=False)

    loading_component = dbc.Collapse([
        html.Div(id=_loading_information),
        dbc.Progress(id=_loading_progress, animated=True, striped=True, max=1.1)
    ], id=_loading_collapse, is_open=False, class_name='mb-1 sticky-top bg-light')

    # overall container
    cont = dbc.Container([
        html.H2('Writing Observer - AskGPT'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
            dbc.Button([html.I(className='fas fa-cog me-1'), 'Advanced'], id=_advanced_toggle),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ], class_name='mb-1'),
        dbc.Collapse(advanced, id=_advanced_collapse, class_name='mb-1'),
        lodrc.LOPanelLayout(
            input_panel,
            panels=[
                {'children': history_favorite_panel, 'width': '30%', 'id': 'history-favorite'},
                {'children': attachment_panel, 'width': '40%', 'id': 'attachment'},
            ],
            shown=['history-favorite'],
            id=panel_layout
        ),
        alert_component,
        html.H3('Student Text', className='mt-1'),
        loading_component,
        dbc.Row(id=grid, class_name='g-4'),
    ], fluid=True)
    return html.Div(cont)


# disbale document date/time options
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='disable_doc_src_datetime'),
    Output(doc_src_date, 'disabled'),
    Output(doc_src_timestamp, 'disabled'),
    Input(doc_src, 'value')
)

# Toggle if the advanced menu collapse is open or not
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleAdvanced'),
    Output(_advanced_collapse, 'is_open'),
    Input(_advanced_toggle, 'n_clicks'),
    State(_advanced_collapse, 'is_open')
)

# send request on websocket
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='send_to_loconnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
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
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='disableQuerySubmitButton'),
    Output(submit, 'disabled'),
    Output(submit_warning_message, 'children'),
    Input(query_input, 'value'),
    Input(_loading_collapse, 'is_open'),
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

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateAlertWithError'),
    Output(alert_text, 'children'),
    Output(alert, 'is_open'),
    Output(alert_error_dump, 'data'),
    Input(lodrc.LOConnectionAIO.ids.error_store(_websocket), 'data')
)

# update student cards based on new data in storage
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateStudentGridOutput'),
    Output(grid, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
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

# update loading information
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateLoadingInformation'),
    Output(_loading_collapse, 'is_open'),
    Output(_loading_progress, 'value'),
    Output(_loading_information, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(history_store, 'data')
)
