from dash import html, dcc, clientside_callback, callback, Output, Input, State, ALL, exceptions, Patch, ctx
import dash_bootstrap_components as dbc

import wo_classroom_text_highlighter.options

_prefix = 'option-preset'
_store = f'{_prefix}-store'
_add_input = f'{_prefix}-add-input'
_add_button = f'{_prefix}-add-button'
_tray = f'{_prefix}-tray'
_set_item = f'{_prefix}-set-item'
_remove_item = f'{_prefix}-remove-item'


def create_layout():
    add_preset = dbc.InputGroup([
        dbc.Input(id=_add_input, placeholder='Preset name', type='text', value=''),
        dbc.Button([
            html.I(className='fas fa-plus me-1'),
            'Preset'
        ], id=_add_button)
    ])
    return html.Div([
        add_preset,
        html.Div(id=_tray),
        dcc.Store(id=_store, data=wo_classroom_text_highlighter.options.PRESETS)
    ])


# disabled add preset when name already exists
clientside_callback(
    '''function (value, curr) {
        if (value.length === 0) { return true; }
        if (Object.keys(curr).includes(value)) { return true; }
        return false;
    }''',
    Output(_add_button, 'disabled'),
    Input(_add_input, 'value'),
    Input(_store, 'data')
)

# clear input on add
clientside_callback(
    '''function (clicks, curr) {
        if (clicks) { return ''; }
        return curr;
    }''',
    Output(_add_input, 'value'),
    Input(_add_button, 'n_clicks'),
    State(_add_input, 'value')
)


def create_tray_item(preset):
    contents = dbc.ButtonGroup([
        dbc.Button(preset, id={'type': _set_item, 'index': preset}),
        dbc.Button(dcc.ConfirmDialogProvider(
            html.I(className='fas fa-close fa-sm'),
            id={'type': _remove_item, 'index': preset},
            message=f'Are you sure you want to delete the `{preset}` preset?'
        ), color='secondary')
    ])
    return contents


@callback(
    Output(_tray, 'children'),
    Input(_store, 'modified_timestamp'),
    State(_store, 'data')
)
def create_tray_items_from_store(ts, data):
    if ts is None:
        raise exceptions.PreventUpdate
    return [html.Span(create_tray_item(preset), className='me-1') for preset in data.keys()]


@callback(
    Output(_store, 'data', allow_duplicate=True),
    Input({'type': _remove_item, 'index': ALL}, 'submit_n_clicks'),
    prevent_initial_call=True
)
def remove_item_from_store(clicks):
    if not ctx.triggered_id or all(c is None for c in clicks):
        raise exceptions.PreventUpdate
    patched_store = Patch()
    del patched_store[ctx.triggered_id['index']]
    return patched_store
