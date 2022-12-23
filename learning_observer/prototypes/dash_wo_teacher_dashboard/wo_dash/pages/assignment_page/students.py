'''
Creates the grid of student cards
'''
# package imports
from learning_observer.dash_wrapper import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
from learning_observer_components import LOConnection
import learning_observer_components as loc  # student cards

# local imports
from . import settings

# define ids for the dashboard
# use a prefix to help ensure we don't double up on IDs (guess what happens if you double up? it breaks)
prefix = 'teacher-dashboard'
student_card = f'{prefix}-student-card'  # individual student card id
student_row = f'{prefix}-student-row'  # overall student row 
student_col = f'{prefix}-student-col'  # individual student card wrapper id
student_grid = f'{prefix}-student-grid'  # overall student grid wrapper id
websocket = f'{prefix}-websocket'  # websocket to connect to the server (eventually)
student_counter = f'{prefix}-student-counter'  # store item for quick access to the number of students
student_store = f'{prefix}-student-store'  # store item for student information
course_store = f'{prefix}-course-store'  # store item for course id
settings_collapse = f'{prefix}-settings-collapse'  # settings menu wrapper
last_updated = f'{prefix}-last-updated'  # data last updated id

assignment_store = f'{prefix}-assignment-info_store'
assignment_name = f'{prefix}-assignment-name'
assignment_desc = f'{prefix}-assignment-description'


def student_dashboard_view(course_id, assignment_id):
    '''Create student dashboard view,

    course_id: id of given course
    assignment_id: id of assignment
    '''
    container = dbc.Container(
        [
            html.Div(
                [
                    # assignment title
                    html.H3(
                        [
                            # document icon with a right bootstrap margin
                            html.I(className='fas fa-file-lines me-2'),
                            html.Span(id=assignment_name),
                        ],
                        className='d-inline'
                    ),
                    # open settings button
                    html.Div(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        [
                                            html.I(id=websocket_status),
                                            html.Span('Last Updated: ', className='ms-2'),
                                            html.Span(id=last_updated)
                                        ],
                                        outline=True, color="dark", className=""
                                    ),
                                    dbc.DropdownMenu(
                                        [
                                            settings.open_btn,
                                            dbc.DropdownMenuItem(
                                                "Logout", 
                                                href="/auth/logout",
                                            ),
                                        ],
                                        group=True,
                                        label="Menu",
                                        className="btn-menu-outline-dark"
                                    )
                                ]
                            )
                        ],
                        className='d-flex align-items-center float-end'
                    ),
                    html.Br(),
                    # assignment description
                    html.P(id=assignment_desc)
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
                        [
                            dbc.Row(
                                id=student_row,
                                # bootstrap gutters-2 (little bit of space between cards) and w(idth)-100(%)
                                class_name='g-2 w-100'
                            ),
                            html.Small(
                                [
                                    'Last Updated: ',
                                    html.Span(id=last_updated)
                                ]
                            )
                        ],
                        id=student_grid,
                        # classname set in callback, default classname should go in the callback
                    )
                ],
                # no spacing between settings and students
                # students already have some space on the sides
                class_name='g-0'
            ),
            # TODO this will likely need the assignment id as well
            # also will eventually need to be updated
            LOConnection(
                id=websocket,
                data_scope={
                    'module': 'writing_observer',
                    'course': course_id,
                    # 'assignment': assignment_id
                },
            ),
            # stores for course and student info + student counter
            dcc.Store(
                id=course_store,
                data=course_id
            ),
            dcc.Store(
                id=assignment_store,
                data=assignment_id
            ),
            dcc.Store(
                id=student_store,
                data=[]
            ),
            dcc.Store(
                id=student_counter,
                data=0
            )
        ],
        fluid=True
    )
    return container


# fetch student info for course
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_students'),
    Output(student_counter, 'data'),
    Output(student_store, 'data'),
    Input(course_store, 'data')
)

# fetch assignment information from server
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='fetch_assignment_info'),
    Output(assignment_name, 'children'),
    Output(assignment_desc, 'children'),
    Input(course_store, 'data'),
    Input(assignment_store, 'data')
)

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
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
    Output({'type': student_card, 'index': ALL}, 'data'),
    Output(last_updated, 'children'),
    Input(websocket, 'message'),
    State({'type': student_card, 'index': ALL}, 'data'),
    State(student_counter, 'data')
)

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


@callback(
    Output(student_row, 'children'),
    Input(student_store, 'data')
)
def create_cards(students):
    # create student cards based on student info
    cards = [
        dbc.Col(
            loc.StudentOverviewCard(
                # pattern matching callback
                id={
                    'type': student_card,
                    'index': s['userId']
                },
                name=s['profile']['name']['fullName'],
                data={
                    'id': s['userId'],
                    'text': {},
                    'highlight': {},
                    'metrics': {},
                    'indicators': {}
                },
                shown=[],
                # adds shadow on hover
                class_name='shadow-card'
            ),
            # pattern matching callback
            id={
                'type': student_col,
                'index': s['userId']
            },
        ) for s in students
    ]
    return cards
