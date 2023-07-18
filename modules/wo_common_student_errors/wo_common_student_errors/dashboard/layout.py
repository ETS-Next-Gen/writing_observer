'''
Define layout for student dashboard view
'''
# package imports
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc
import plotly.express as px

from dash import clientside_callback, ClientsideFunction, Output, Input, State, html, dcc

# local imports
from . import activity, individual

prefix = 'common-student-errors'
websocket = f'{prefix}-websocket'
ws_store = f'{prefix}-ws-store'

error_per_length = f'{prefix}-errors-per-length-graph'
error_per_length_tooltip = f'{prefix}-errors-per-length-tooltip'
error_per_length_figure = px.scatter(
    x=[0], y=[0], text=[''], title='Number of errors compared to text length',
    labels=dict(x='Text length (words)', y='Total Errors')
)
error_per_length_figure.update_layout(clickmode='event+select')
error_per_length_figure.update_traces(hoverinfo='none', hovertemplate=None, marker_size=24, textfont=dict(color='white'), textposition='middle center')

categorical_errors = f'{prefix}-categorical-errors'


def layout():
    headers = ['Student']
    [headers.append(category) for category in individual.colors.keys()]

    tooltip = dcc.Tooltip(id=error_per_length_tooltip, direction='bottom')
    overall_view = dbc.Col([
        activity.student_activity(),
        dcc.Graph(
            id=error_per_length,
            figure=error_per_length_figure,
            clear_on_unhover=True
        ),
        tooltip,
        html.Div([
            dbc.Table([
                html.Thead((html.Tr([html.Th(h) for h in headers]))),
                html.Tbody(id=categorical_errors)
            ], hover=True),
        ])
    ], md=9, lg=8, xl=7, xxl=6)

    individal_view = dbc.Col([
        individual.layout
    ], md=3, lg=4, xl=5, xxl=6)

    cont = dbc.Container([
        dcc.Store(ws_store, data={}),
        lodrc.LOConnection(id=websocket),
        dbc.Row([
            overall_view,
            individal_view
        ])
    ], fluid=True)
    return cont


clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='send_to_loconnection'),
    Output(websocket, 'send'),
    Input(websocket, 'state'),  # used for initial setup
    Input('_pages_location', 'hash')
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='update_hash_via_graph'),
    Output('_pages_location', 'hash'),
    Input(error_per_length, 'selectedData'),
    State(ws_store, 'data')
)

clientside_callback(
    '''
    function(message) {
        const data = JSON.parse(message.data)
        console.log(data)
        return data
    }
    ''',
    Output(ws_store, 'data'),
    Input(websocket, 'message')
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_activity'),
    Output(activity.inactive, 'children'),
    Output(activity.active, 'children'),
    Input(ws_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_student_error'),
    Output(individual.student, 'children'),
    Output(individual.text, 'children'),
    Output(individual.errors, 'children'),
    Output(individual.error_sunburst, 'extendData'),
    Input(ws_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='update_graph_hover'),
    Output(error_per_length_tooltip, 'show'),
    Output(error_per_length_tooltip, 'bbox'),
    Output(error_per_length_tooltip, 'children'),
    Input(error_per_length, 'hoverData'),
    Input(ws_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_error_graph'),
    Output(error_per_length, 'extendData'),
    Input(ws_store, 'data'),
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_categorical_errors'),
    Output(categorical_errors, 'children'),
    Input(ws_store, 'data')
)
