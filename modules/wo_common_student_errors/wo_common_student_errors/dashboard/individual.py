'''
'''
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

prefix = 'individual-student-errors'
student = f'{prefix}-student'
text = f'{prefix}-text'
errors = f'{prefix}-errors'


colors = {
    'Error': 'white',  # white
    'Capitalization': '#f3969a',  # light pink
    'Grammar': '#56cc9d',  # turquoise
    'Possible Typo': '#6cc3d5',  # sky blue
    'Punctuation': '#ffce67',  # yellow
    'Semantics': '#ff7851',  # orange
    'Spelling': '#D9A9F5',  # lilac purple
    'Style': '#9EF5D9',  # mint green
    'Typography': '#87CEEB',  # baby blue
    'Usage': '#FFB347',  # soft orange
    'Word Boundaries': '#F5F0A9',  # light yellow
}

error_sunburst = f'{prefix}-errors-sunburst'
error_sunburst_figure = go.Figure(go.Sunburst(
    labels=[],
    parents=[],
    values=[],
    marker=dict(
        colors=pd.Series(colors)
    ),
    branchvalues='total'
))
error_sunburst_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0))

layout = html.Div([
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
], className='vh-100')
