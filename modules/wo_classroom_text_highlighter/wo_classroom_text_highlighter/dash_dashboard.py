'''
This file creates the layout and defines any callbacks
for the classroom highlight dashboard.
'''
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
import dash_renderjson
import lo_dash_react_components as lodrc

import learning_observer.settings
import wo_classroom_text_highlighter.options
import wo_classroom_text_highlighter.preset_component

DEBUG_FLAG = learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV

_prefix = 'wo-classroom-text-highlighter'
_namespace = 'wo_classroom_text_highlighter'
_websocket = f'{_prefix}-websocket'
_output = f'{_prefix}-output'

# Option components
_options_toggle = f'{_prefix}-options-toggle'
_options_collapse = f'{_prefix}-options-collapse'
# TODO abstract these into a more generic options component
_options_prefix = f'{_prefix}-options'
_options_width = f'{_options_prefix}-width'
_options_height = f'{_options_prefix}-height'
_options_hide_header = f'{_options_prefix}-hide-names'
_options_text_information = f'{_options_prefix}-text-information'

options_component = [
    html.H4('View Options'),
    dbc.Label('Students per row'),
    dbc.Input(type='number', min=1, max=10, value=3, step=1, id=_options_width),
    dbc.Label('Height of student tile'),
    dcc.Slider(min=100, max=800, marks=None, value=500, id=_options_height),
    dbc.Label('Student name headers'),
    dbc.Switch(value=True, id=_options_hide_header, label='Show/Hide'),
    html.H4('Highlight Options'),
    wo_classroom_text_highlighter.preset_component.create_layout(),
    lodrc.WOSettings(id=_options_text_information, options=wo_classroom_text_highlighter.options.OPTIONS, className='table table-striped align-middle')
]

# Alert Component
_alert = f'{_prefix}-alert'
_alert_text = f'{_prefix}-alert-text'
_alert_error_dump = f'{_prefix}-alert-error-dump'

alert_component = dbc.Alert([
    html.Div(id=_alert_text),
    html.Div(dash_renderjson.DashRenderjson(id=_alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
], id=_alert, color='danger', is_open=False)


def layout():
    '''
    Function to define the page's layout.
    '''
    page_layout = html.Div([
        html.H1('Writing Observer - Classroom Text Highlighter'),
        alert_component,
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
            dbc.Button([
                html.I(className='fas fa-cog me-1'),
                'Highlight Options'
            ], id=_options_toggle),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ], class_name='sticky-top mb-1'),
        dbc.Offcanvas(options_component, id=_options_collapse, scrollable=True, title='Settings'),
        html.Div(id=_output, className='d-flex justify-content-between flex-wrap')
    ])
    return page_layout


# Send the initial state based on the url hash to LO.
# If this is not included, nothing will be returned from
# the communication protocol.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(_options_text_information, 'options')
)

# Build the UI based on what we've received from the
# communicaton protocol
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='populateOutput'),
    Output(_output, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_options_text_information, 'options'),
    Input(_options_width, 'value'),
    Input(_options_height, 'value'),
    Input(_options_hide_header, 'value'),
)

# Toggle if the options collapse is open or not
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleOptions'),
    Output(_options_collapse, 'is_open'),
    Input(_options_toggle, 'n_clicks'),
    State(_options_collapse, 'is_open')
)

# Adjust student tile size
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='adjustTileSize'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'style'),
    Input(_options_width, 'value'),
    Input(_options_height, 'value'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# Handle showing or hiding the student tile header
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='showHideHeader'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'showHeader'),
    Input(_options_hide_header, 'value'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# When options change, update the current option hash for all students.
# When the option hash is different from the students internal option hash
# a loading class is applied to each student tile.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateCurrentOptionHash'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'currentOptionHash'),
    Input(_options_text_information, 'options'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# Update the alert component with any errors that come through
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateAlertWithError'),
    Output(_alert_text, 'children'),
    Output(_alert, 'is_open'),
    Output(_alert_error_dump, 'data'),
    Input(lodrc.LOConnectionAIO.ids.error_store(_websocket), 'data')
)

# Save options as preset
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='addPreset'),
    Output(wo_classroom_text_highlighter.preset_component._store, 'data'),
    Input(wo_classroom_text_highlighter.preset_component._add_button, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._add_input, 'value'),
    State(_options_text_information, 'options'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data')
)

# Apply clicked preset
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='applyPreset'),
    Output(_options_text_information, 'options'),
    Input({'type': wo_classroom_text_highlighter.preset_component._set_item, 'index': ALL}, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data'),
    prevent_initial_call=True
)
