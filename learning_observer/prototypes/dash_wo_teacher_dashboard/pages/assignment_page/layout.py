# package imports
import dash
from dash import html

# local imports
from components.course import Course
from .teacher_dashboard import create_teacher_dashboard

dash.register_page(
    __name__,
    path_template='/dashboard',
    title='Dashboard'
)

def layout():
    role = 'teacher'
    course_id = 1
    course = Course(course_id, role)
    dashboard = create_teacher_dashboard(course, course.assignments[0])
    layout = html.Div(
        [
            dashboard
        ]
    )
    return layout
