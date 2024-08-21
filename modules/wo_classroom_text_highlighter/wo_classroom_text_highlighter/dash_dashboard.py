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
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

import wo_classroom_text_highlighter.options
import wo_classroom_text_highlighter.preset_component

_prefix = 'wo-classroom-text-highlighter'
_namespace = 'wo_classroom_text_highlighter'
_websocket = f'{_prefix}-websocket'
_output = f'{_prefix}-output'

_options_toggle = f'{_prefix}-options-toggle'
_options_collapse = f'{_prefix}-options-collapse'
# TODO abstract these into a more generic options component
_options_prefix = f'{_prefix}-options'
_options_width = f'{_options_prefix}-width'
_options_height = f'{_options_prefix}-height'
_options_hide_header = f'{_options_prefix}-hide-names'
_options_text_information = f'{_options_prefix}-text-information'

options_component = [
    dbc.Label('Students per row'),
    dbc.Input(type='number', min=1, max=10, value=3, step=1, id=_options_width),
    dbc.Label('Height'),
    dcc.Slider(min=100, max=800, marks=None, value=500, id=_options_height),
    dbc.Label('Headers'),
    dbc.Switch(value=True, id=_options_hide_header, label='Show/Hide'),
    dbc.Label('Text information'),
    wo_classroom_text_highlighter.preset_component.create_layout(),
    lodrc.WOSettings(id=_options_text_information, options=wo_classroom_text_highlighter.options.OPTIONS)
]

def layout():
    '''
    Function to define the page's layout.
    '''
    page_layout = html.Div([
        html.H1('Writing Observer Classroom Text Highlighter'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
            dbc.Button(html.I(className='fas fa-cog'), id=_options_toggle),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ]),
        dbc.Collapse(options_component, id=_options_collapse),
        html.Div(id=_output, className='d-flex justify-content-around flex-wrap')
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
# This clientside callback and the serverside callback below are
# the same
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

# Handle showing/hiding the student tile header
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='showHideHeader'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'showHeader'),
    Input(_options_hide_header, 'value'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# When options change, update the current option hash for all students.
# when the option hash is different from the students internal option hash
# a loading class is applied
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateCurrentOptionHash'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'currentOptionHash'),
    Input(_options_text_information, 'options'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# Save preset
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='addPreset'),
    Output(wo_classroom_text_highlighter.preset_component._store, 'data'),
    Input(wo_classroom_text_highlighter.preset_component._add_button, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._add_input, 'value'),
    State(_options_text_information, 'options'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data')
)

# apply preset
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='applyPreset'),
    Output(_options_text_information, 'options'),
    Input({'type': wo_classroom_text_highlighter.preset_component._set_item, 'index': ALL}, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data'),
    prevent_initial_call=True
)
