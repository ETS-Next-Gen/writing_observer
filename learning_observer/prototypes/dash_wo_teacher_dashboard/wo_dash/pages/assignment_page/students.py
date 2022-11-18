'''
Creates the grid of student cards
'''
# package imports
from learning_observer.dash_wrapper import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State, ALL, exceptions as dash_e
import dash_bootstrap_components as dbc
from learning_observer_components import LOConnection
import learning_observer_components as loc  # student cards

# local imports
from . import settings, settings_defaults, settings_options as so

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
                            settings.open_btn
                        ],
                        className='float-end'
                    ),
                    html.Br(),
                    # assignment description
                    html.P(id=assignment_desc)
                ]
            ),
            html.Small(
                [
                    'Last Updated: ',
                    html.Span(id=last_updated)
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
                            id=student_row,
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
            LOConnection(id=websocket),
            # stores for course and student info + student counter
            dcc.Store(id=course_store),
            dcc.Store(id=assignment_store),
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


# set hash parameters
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_course_assignment'),
    Output(course_store, 'data'),
    Output(assignment_store, 'data'),
    Input('_pages_location', 'hash')
)

# set the websocket data_scope
clientside_callback(
    """
    function(course, assignment) {
        const ret = {"module": "latest_data", "course": course};
        return ret;
    }
    """,
    Output(websocket, 'data_scope'),
    Input(course_store, 'data'),
    Input(assignment_store, 'data')
)

# fetch student info for course
# TODO fix this to pull the roster information better
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
    Input(settings.open_btn, 'n_clicks'),
    Input(settings.close_settings, 'n_clicks'),
    State(settings_collapse, 'is_open'),
    State(student_counter, 'data')
)

# Update data from websocket
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
    Output({'type': student_card, 'index': ALL}, 'data'),
    Output(last_updated, 'children'),
    # Output(student_counter, 'data'),
    # Output(student_store, 'data'),
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
    Input(settings.checklist, 'value'),
    Input(settings.metric_checklist, 'value'),
    Input(settings.text_radioitems, 'value'),
    Input(settings.highlight_checklist, 'value'),
    Input(settings.indicator_checklist, 'value'),
    State(student_counter, 'data')
)


# highlight text
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='highlight_text'),
    Output(settings.dummy, 'style'),
    Input(settings.checklist, 'value'),
    Input(settings.highlight_checklist, 'value'),
    Input({'type': student_card, 'index': ALL}, 'data'),
    State(settings.highlight_checklist, 'options')
)


@callback(
    output=dict(
        sort_by_options=Output(settings.sort_by_checklist, 'options'),
        metric_options=Output(settings.metric_checklist, 'options'),
        metric_value=Output(settings.metric_checklist, 'value'),
        text_options=Output(settings.text_radioitems, 'options'),
        text_value=Output(settings.text_radioitems, 'value'),
        highlight_options=Output(settings.highlight_checklist, 'options'),
        highlight_value=Output(settings.highlight_checklist, 'value'),
        indicator_options=Output(settings.indicator_checklist, 'options'),
        indicator_value=Output(settings.indicator_checklist, 'value'),
    ),
    inputs=dict(
        course=Input(course_store, 'data'),
        assignment=Input(assignment_store, 'data')
    )    
)
def fill_in_settings(course, assignment):
    # populate all settings based on assignment or default

    # TODO grab the options or type from assignment
    # if options (obj) set opt to assignment options
    # if type (string) set opt to settings_default.type
    opt = settings_defaults.argumentative
    
    ret = dict(
        sort_by_options=[so.sort_by_options[o] for o in opt['sort_by']['options']],
        metric_options=[so.metric_options[o] for o in opt['metrics']['options']],
        metric_value=opt['metrics']['selected'],
        text_options=[so.text_options[o] for o in opt['text']['options']],
        text_value=opt['text']['selected'],
        highlight_options=[so.highlight_options[o] for o in opt['highlight']['options']],
        highlight_value=opt['highlight']['selected'],
        indicator_options=[so.indicator_options[o] for o in opt['indicators']['options']],
        indicator_value=opt['indicators']['selected'],
    )
    return ret


@callback(
    Output(student_row, 'children'),
    Input(student_store, 'data')
)
def create_cards(students):
    # create student cards based on student info

    # TODO if the card data exists in the student_store,
    # we want to include it in the initial loading of the card
    # this will require the same parser we create for updates
    # i.e. the same code for both js and python
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
