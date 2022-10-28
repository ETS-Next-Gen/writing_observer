'''
Define layout for student dashboard view
'''
# package imports
import learning_observer.dash_wrapper as dash
import dash_bootstrap_components as dbc

# local imports
from .students import student_dashboard_view

dash.register_page(
    __name__,
    path_template='/dashboard',
    title='Dashboard'
)


# passing empty parameters will automatigically be used as query strings
# see: https://dash.plotly.com/urls#query-strings
def layout(course_id=None, assignment_id=None):
    layout = dbc.Spinner(
        student_dashboard_view(course_id, assignment_id),
        color='primary'
    )
    return layout
