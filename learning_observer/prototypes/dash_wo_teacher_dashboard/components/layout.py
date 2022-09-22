'''
Define overall UI layout
'''
# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc

# local imports
from .navbar import navbar


# create layout
def serve_layout():
    return html.Div(
        [
            navbar,
            dbc.Container(
                dash.page_container,
                # top/bottom bootstrap margin
                class_name='my-2',
                # take up full scren width
                fluid=True
            )
        ],
        # wrapper for styling dcc components as Bootstrap
        className='dbc'
    )
