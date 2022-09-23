'''
Creates the grid of student cards
'''
import pathlib

# package imports
from learning_observer.dash_wrapper import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
# from dash_extensions import WebSocket
import learning_observer_components as loc  # student cards
import json
import os

# local imports
from . import settings

# read in raw data (no websocket connection)
# used for demo, sample.json is output from the data_preprocessing.py script
data_path = pathlib.Path(__file__).parent.parent.parent.joinpath('uncommitted', 'sample.json')
with open(data_path, 'r') as f_obj:
    data = json.load(f_obj)

# define ids for the dashboard
# use a prefix to help ensure we don't double up on IDs (guess what happens if you double up? it breaks)
prefix = 'teacher-dashboard'
student_card = f'{prefix}-student-card'  # individual student card id
student_col = f'{prefix}-student_col'  # individual student card wrapper id
student_grid = f'{prefix}-student-grid'  # overall student grid wrapper id
websocket = f'{prefix}-websocket'  # websocket to connect to the server (eventually)
student_counter = f'{prefix}-student-counter'  # store item for quick access to the number of students
settings_collapse = f'{prefix}-settings-collapse'  # settings menu wrapper


def student_dashboard_view(assignment, students):
    '''Create student dashboard view,

    assignment: assignment object
    students: list of student objects
    '''
    # prep assignment description
    description = []
    for e in assignment.description.split('\n'):
        description.append(e)
        description.append(html.Br())
    description.pop()

    container = dbc.Container(
        [
            html.Div(
                [
                    # assignment title
                    html.H3(
                        [
                            # document icon with a right bootstrap margin
                            html.I(className='fas fa-file-lines me-2'),
                            assignment.name
                        ],
                        className='d-inline'
                    ),
                    # open settings button
                    html.Div(
                        [
                            settings.open_btn
                        ],
                        className='float-end'
                    ),
                    html.Br(),
                    # assignment description
                    html.P(description)
                ]
            ),
            dbc.Row(
                [
                    # settings panel wrapper
                    dbc.Collapse(
                        dbc.Col(
                            settings.panel,
                            # bootstrap use 100% of (w)idth and (h)eight
                            class_name='w-100 h-100'
                        ),
                        id=settings_collapse,
                        # bootstrap collapse and grid sizing
                        class_name='collapse-horizontal col-xxl-3 col-lg-4 col-md-6',
                        # default open/close
                        is_open=False
                    ),
                    # overall student grid wrapp
                    dbc.Col(
                        dbc.Row(
                            [
                                # for each student, create a new card
                                # pass in sample data
                                # student card wrapper
                                dbc.Col(
                                    loc.StudentOverviewCard(
                                        # pattern matching callback
                                        id={
                                            'type': student_card,
                                            'index': s['id']
                                        },
                                        name=s['name'],
                                        data=data[i],
                                        shown=[],
                                        # adds shadow on hover
                                        class_name='shadow-card'
                                    ),
                                    # pattern matching callback
                                    id={
                                        'type': student_col,
                                        'index': s['id']
                                    },
                                ) for i, s in enumerate(students)
                            ],
                            # bootstrap gutters-2 (little bit of space between cards) and w(idth)-100(%)
                            class_name='g-2 w-100'
                        ),
                        id=student_grid,
                        # classname set in callback, default classname should go in the callback
                    )
                ],
                # no spacing between settings and students
                # students already have some space on the sides
                class_name='g-0'
            ),
            # TODO uncomment this out for the websocket connection
            # WebSocket(
            #     id=websocket,
            #     url=f'ws://127.0.0.1:5000/courses/students/{len(students)}'
            # ),
            # store for the number of students
            dcc.Store(
                id=student_counter,
                data=len(students)
            )
        ],
        fluid=True
    )
    return container


# open the settings menu
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_settings'),
    Output(settings_collapse, 'is_open'),
    Output({'type': student_col, 'index': ALL}, 'class_name'),
    Output(student_grid, 'class_name'),
    Input(settings.show_hide_settings_open, 'n_clicks'),
    Input(settings.close_settings, 'n_clicks'),
    State(settings_collapse, 'is_open'),
    State(student_counter, 'data')
)

# Update data from websocket
# TODO uncomment this out for the connection
# clientside_callback(
#     ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
#     Output({'type': student_card, 'index': ALL}, 'data'),
#     Input(websocket, 'message'),
#     State({'type': student_card, 'index': ALL}, 'data'),
#     State(student_counter, 'data')
# )

# Sort students by indicator values
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='sort_students'),
    Output({'type': student_col, 'index': ALL}, 'style'),
    Input(settings.sort_by_checklist, 'value'),
    Input(settings.sort_toggle, 'value'),
    Input({'type': student_card, 'index': ALL}, 'data'),
    State(settings.sort_by_checklist, 'options'),
    State(student_counter, 'data')
)

# hide/show attributes on student cards
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='show_hide_data'),
    Output({'type': student_card, 'index': ALL}, 'shown'),
    Input(settings.show_hide_settings_checklist, 'value'),
    Input(settings.show_hide_settings_metric_checklist, 'value'),
    Input(settings.show_hide_settings_text_radioitems, 'value'),
    Input(settings.show_hide_settings_highlight_checklist, 'value'),
    Input(settings.show_hide_settings_indicator_checklist, 'value'),
    State(student_counter, 'data')
)
