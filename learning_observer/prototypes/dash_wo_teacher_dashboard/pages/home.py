# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc


dash.register_page(
    __name__,
    path='/',
    redirect_from=['/home'],
    title='Learning Observer'
)

layout = html.Div(
    [
        html.H1('Welcome to Learning Observer'),
        html.A('Dashboard', href='/dashboard')
    ]
)
