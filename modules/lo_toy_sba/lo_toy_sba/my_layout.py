from dash import html, dcc
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

def my_layout(_websocket, _websocket_storage, _output):
    '''
    This is the layout for the static part of your dashboard which
    is loaded when the page first loads.

    * The data would be populated in a div with id _output.
    * We pass the _websocket so we can render a component letting us know when things updated
    * We pass the _websocket_storage, although we really should bubble that up.
    '''
    page_layout = html.Div(children=[
        html.H1(children='Toy-SBA Module'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionStatusAIO(aio_id=_websocket)),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ]),
        dcc.Store(id=_websocket_storage),
        html.H2('Output from reducers'),
        html.Div(id=_output)
    ])
    return page_layout


def my_data_layout(data):
    '''
    This is the layout for the changing part of your dashboard
    populated from the data.
    '''
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
