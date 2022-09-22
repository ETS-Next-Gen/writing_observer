'''
Navbar UI element
'''
# package imports
from dash import html
import dash_bootstrap_components as dbc

navbar = html.Div(
    dbc.Navbar(
        [
            dbc.Container(
                [
                    dbc.NavbarBrand(
                        'Learning Observer',
                        href='/'
                    )
                ],
                fluid=True
            )
        ],
        sticky='fixed',
        color='primary',
        dark=True
    )
)
