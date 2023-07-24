'''
'''
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from . import colors

prefix = 'individual-student-errors'
student = f'{prefix}-student'
text = f'{prefix}-text'
errors = f'{prefix}-errors'

error_sunburst = f'{prefix}-errors-sunburst'
error_sunburst_figure = go.Figure(go.Sunburst(
    ids=[],
    labels=[],
    parents=[],
    values=[],
    marker=dict(
        colors=pd.Series(colors.colors)
    ),
    branchvalues='total'
))
error_sunburst_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0))

layout = html.Div([
    html.Div([
        html.H4(id=student),
        html.Div(id=text),
        dbc.Row([
            dbc.Col(html.Div(id=errors), sm=6, class_name='h-100 overflow-auto'),
            dbc.Col(
                dcc.Graph(id=error_sunburst, figure=error_sunburst_figure, style={'height': '100%'}),
                sm=6,
                class_name='h-100'
            )
        ], class_name='individual-error-row')
    ], className='loaded'),
    html.Div(dbc.Spinner(), className='loading')
], id=prefix)
