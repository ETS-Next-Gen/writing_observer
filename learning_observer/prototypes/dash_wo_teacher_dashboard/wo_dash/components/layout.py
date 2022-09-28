'''
Define overall UI layout
'''
# package imports
import learning_observer.dash_wrapper as dash
from learning_observer.dash_wrapper import html
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
