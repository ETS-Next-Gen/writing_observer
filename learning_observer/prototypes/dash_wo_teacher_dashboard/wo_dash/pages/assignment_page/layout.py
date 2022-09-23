'''
Define layout for student dashboard view
'''
# package imports
import dash
import dash_bootstrap_components as dbc

# local imports
from .students import student_dashboard_view
from components.course import Course

dash.register_page(
    __name__,
    path_template='/dashboard',
    title='Dashboard'
)


def layout():
    # create a fake class
    course_id = 1
    course = Course(course_id)

    layout = dbc.Spinner(
        student_dashboard_view(course.assignments[0], course.students),
        color='primary'
    )
    return layout
