'''This creates the input and clickable badges for different
presets the user wants displayed.
TODO create a react component that does this
'''
import asyncio
from dash import html, dcc, clientside_callback, callback, Output, Input, State, ALL, exceptions, Patch, ctx
import dash_bootstrap_components as dbc

import learning_observer.constants as c
import learning_observer.dash_integration
import learning_observer.kvs
import learning_observer.stream_analytics.helpers as sa_helpers

import wo_classroom_text_highlighter.options

_prefix = 'option-preset'
_store = f'{_prefix}-store'
_add_input = f'{_prefix}-add-input'
_add_help = f'{_prefix}-add-help'
_add_button = f'{_prefix}-add-button'
_tray = f'{_prefix}-tray'
_set_item = f'{_prefix}-set-item'
_remove_item = f'{_prefix}-remove-item'

# TODO many dashboards will likely use some form of presets tied to the user
# this ought to be generic enough that we can easily add it to each dashboard
def preset_components():
    pass


async def get_preset_components():
    return wo_classroom_text_highlighter.options.PRESETS
    current_user = await learning_observer.dash_integration.get_active_user_from_dash()
    if c.USER_ID not in current_user or not current_user[c.USER_ID]:
        raise KeyError(f'User id not found in active user')
    key = _make_key(current_user[c.USER_ID])
    kvs = learning_observer.kvs.KVS()
    presets = await kvs[key]
    if presets is None:
        presets = wo_classroom_text_highlighter.options.PRESETS
        await kvs.set(key, presets)
    return presets


def _make_key(user_id):
    return sa_helpers.make_key(
        preset_components,
        {sa_helpers.KeyField.STUDENT: user_id},
        sa_helpers.KeyStateType.INTERNAL
    )


async def create_layout():
    kvs_presets = await get_preset_components()
    add_preset = dbc.InputGroup([
        dbc.Input(id=_add_input, placeholder='Preset name', type='text', value=''),
        dbc.InputGroupText(html.I(className='fas fa-circle-question'), id=_add_help),
        dbc.Tooltip(
            'Save the current selected information as a preset for quick use in the future.',
            target=_add_help
        ),
        dbc.Button([
            html.I(className='fas fa-plus me-1'),
            'Preset'
        ], id=_add_button)
    ], class_name='mb-1')
    return html.Div([
        add_preset,
        html.Div(id=_tray),
        dcc.Store(id=_store, data=kvs_presets, storage_type='local')
    ], id=_prefix)


# disabled add preset when name already exists
clientside_callback(
    '''function (value, curr) {
        if (value.length === 0) { return true; }
        if (Object.keys(curr).includes(value)) { return true; }
        return false;
    }''',
    Output(_add_button, 'disabled'),
    Input(_add_input, 'value'),
    State(_store, 'data')
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
    if preset == wo_classroom_text_highlighter.options.deselect_all:
        return dbc.Button(preset, id={'type': _set_item, 'index': preset}, color='warning')
    contents = dbc.ButtonGroup([
        dbc.Button(preset, id={'type': _set_item, 'index': preset}),
        dcc.ConfirmDialogProvider(
            dbc.Button(html.I(className='fas fa-trash fa-xs'), color='secondary'),
            id={'type': _remove_item, 'index': preset},
            message=f'Are you sure you want to delete the `{preset}` preset?'
        )
    ], class_name='preset')
    return contents


@callback(
    Output(_tray, 'children'),
    Input(_store, 'modified_timestamp'),
    State(_store, 'data')
)
def create_tray_items_from_store(ts, data):
    if ts is None and data is None:
        raise exceptions.PreventUpdate
    return [html.Div(create_tray_item(preset), className='d-inline-block me-1 mb-1') for preset in reversed(data.keys())]


# TODO we should fetch from redis and then reset in redis
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
