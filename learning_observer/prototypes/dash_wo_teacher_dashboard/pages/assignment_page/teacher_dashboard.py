# package imports
import dash_bootstrap_components as dbc

# local imports
from .students import create_student_tab

def create_teacher_dashboard(course, assignment):
    dashboard = dbc.Spinner(
        create_student_tab(assignment, course.students),
        color='primary'
    )
    return dashboard
