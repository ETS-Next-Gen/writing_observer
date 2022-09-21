# package imports
import dash
from dash import html

dash.register_page(__name__, path='/404')

layout = html.Div('Not found')
