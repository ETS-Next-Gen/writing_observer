'''
Define custom 404 not found page
This file must be called not_found_404.py to automatically work with Dash
'''
# package imports
import learning_observer.dash_wrapper as dash
from learning_observer.dash_wrapper import html

dash.register_page(__name__, path='/404')

layout = html.Div('Not found')
