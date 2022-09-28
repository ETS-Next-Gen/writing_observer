'''
Register Home page of dash application
'''
# package imports
import learning_observer.dash_wrapper as dash
from learning_observer.dash_wrapper import html

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
