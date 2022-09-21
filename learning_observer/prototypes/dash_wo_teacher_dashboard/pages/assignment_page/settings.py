# package imports
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc

prefix = 'teacher-dashboard-settings'
# settings ids
close_settings = f'{prefix}-close'
sort_by_checklist = f'{prefix}-sort-by-checklist'
sort_toggle = f'{prefix}-sort-by-toggle'
sort_icon = f'{prefix}-sort-by-icon'
sort_label = f'{prefix}-sort-by-label'
sort_reset = f'{prefix}-sort-by-reset'

show_hide_settings_open = f'{prefix}-show-hide-open-button'
show_hide_settings_offcanvas = f'{prefix}-show-hide-offcanvcas'
show_hide_settings_checklist = f'{prefix}-show-hide-checklist'

show_hide_settings_metric_collapse = f'{prefix}-show-hide-metric-collapse'
show_hide_settings_metric_checklist = f'{prefix}-show-hide-metric-checklist'

show_hide_settings_text_collapse = f'{prefix}-show-hide-text-collapse'
show_hide_settings_text_radioitems = f'{prefix}-show-hide-text-radioitems'

show_hide_settings_highlight_collapse = f'{prefix}-show-hide-highlight-collapse'
show_hide_settings_highlight_checklist = f'{prefix}-show-hide-highlight-radioitems'

show_hide_settings_indicator_collapse = f'{prefix}-show-hide-indicator-collapse'
show_hide_settings_indicator_checklist = f'{prefix}-show-hide-indicator-checklist'

open_btn = dbc.Button(
    [
        html.I(className='fas fa-gear'),
        html.Span('Settings', className='ms-1 d-none d-lg-inline'),
    ],
    class_name='btn btn-secondary',
    id=show_hide_settings_open,
    title='Open settings menu to show or hide different student attributes'
)

panel = dbc.Card(
    [
        html.Div(
            [
                html.H4(
                    [
                        html.I(className='fas fa-gear me-2'),
                        'Settings'
                    ], className='d-inline'
                ),
                dbc.Button(
                    html.I(className='fas fa-xmark'),
                    color='white',
                    class_name='float-end text-body',
                    id=close_settings
                )
            ],
            className='m-2'
        ),
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    dbc.Card(
                        [
                            dcc.Checklist(
                                options=[
                                    {'label': 'Transition Words', 'value': 'transitions'},
                                    {'label': 'Academic Language', 'value': 'academiclanguage'},
                                    {'label': 'Argument Language', 'value': 'argumentlanguage'},
                                    {'label': 'Attributions', 'value': 'attributions'},
                                    {'label': 'Citations', 'value': 'cites'},
                                    {'label': 'Sources', 'value': 'sources'}
                                ],
                                value=[],
                                id=sort_by_checklist,
                                labelClassName='form-check nested-form',
                                inputClassName='form-check-input'
                            ),
                            html.Div(
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            dcc.Checklist(
                                                options=[
                                                    {
                                                        'value': 'checked',
                                                        'label': html.Span(
                                                            [
                                                                html.I(id=sort_icon),
                                                                html.Span(
                                                                    'None',
                                                                    id=sort_label,
                                                                    className='ms-1'
                                                                )
                                                            ]
                                                        )
                                                    }
                                                ],
                                                value=['checked'],
                                                id=sort_toggle,
                                                inputClassName='d-none',
                                                className='d-inline',
                                            ),
                                            outline=True,
                                            color='primary',
                                            title='Arrange students by attributes',
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(className='fas fa-rotate me-1'),
                                                'Reset Sort'
                                            ],
                                            id=sort_reset,
                                            outline=True,
                                            color='primary'
                                        )
                                    ],
                                    size='sm',
                                    class_name='float-end d-inline'
                                ),
                                className='mt-1'
                            )
                        ],
                        class_name='border-0'
                    ),
                    title='Sort by',
                ),
                dbc.AccordionItem(
                    [
                        dcc.Checklist(
                                    options=[
                                        {
                                            'label': html.Span(
                                                [
                                                    html.Span(
                                                        [
                                                            html.I(className='fas fa-hashtag me-1'),
                                                            'Metrics overview'
                                                        ],
                                                        className='font-size-lg'
                                                    ),
                                                    dbc.Collapse(
                                                        dcc.Checklist(
                                                            options=[
                                                                {
                                                                    'label': dbc.Badge(
                                                                        '# sentences',
                                                                        color='info',
                                                                        title='Total number of sentences'
                                                                    ),
                                                                    'value': 'sentences'
                                                                },
                                                                {
                                                                    'label': dbc.Badge(
                                                                        '# adverbs',
                                                                        color='info',
                                                                        title='Total number of adverbs'
                                                                    ),
                                                                    'value': 'adverbs'
                                                                },
                                                                {
                                                                    'label': dbc.Badge(
                                                                        '# adjectives',
                                                                        color='info',
                                                                        title='Total number of adjectives'
                                                                    ),
                                                                    'value': 'adjectives'
                                                                },
                                                                {
                                                                    'label': dbc.Badge(
                                                                        '# quoted words',
                                                                        color='info',
                                                                        title='Total number of quoted words'
                                                                    ),
                                                                    'value': 'quotedwords'
                                                                },
                                                                {
                                                                    'label': dbc.Badge(
                                                                        '# minutes on task',
                                                                        color='info',
                                                                        title='Total minutes on task'
                                                                    ),
                                                                    'value': 'timeontask'
                                                                },
                                                                {
                                                                    'label': dbc.Badge(
                                                                        '# words in last 5 min',
                                                                        color='info',
                                                                        title='Total words in last 5 minutes'
                                                                    ),
                                                                    'value': 'recentwords'
                                                                },
                                                            ],
                                                            value=['sentences', 'timeontask'],
                                                            id=show_hide_settings_metric_checklist,
                                                            labelClassName='form-check nested-form',
                                                            inputClassName='form-check-input'
                                                        ),
                                                        id=show_hide_settings_metric_collapse,
                                                    )
                                                ],
                                            ),
                                            'value': 'metrics'
                                        },
                                        {
                                            'label': html.Span(
                                                [
                                                    html.Span(
                                                        [
                                                            html.I(className='fas fa-file me-1'),
                                                            'Text',
                                                        ],
                                                        className='font-size-lg'
                                                    ),
                                                    dbc.Collapse(
                                                        dcc.RadioItems(
                                                            options=[
                                                                {
                                                                    'label': 'Student text',
                                                                    'value': 'studenttext'
                                                                },
                                                                # {
                                                                #     'label': 'Emotion words',
                                                                #     'value': 'emotionwords'
                                                                # },
                                                                # {
                                                                #     'label': 'Concrete details',
                                                                #     'value': 'concretedetails'
                                                                # },
                                                                {
                                                                    'label': 'Argument words',
                                                                    'value': 'argumentwords'
                                                                },
                                                                {
                                                                    'label': 'Transitions used',
                                                                    'value': 'transitionwords'
                                                                }
                                                            ],
                                                            value='studenttext',
                                                            id=show_hide_settings_text_radioitems,
                                                            labelClassName='form-check nested-form',
                                                            inputClassName='form-check-input'
                                                        ),
                                                        id=show_hide_settings_text_collapse,
                                                    )
                                                ],
                                            ),
                                            'value': 'text'
                                        },
                                        {
                                            'label': html.Span(
                                                [
                                                    html.Span(
                                                        [
                                                            html.I(className='fas fa-highlighter fa-flip-horizontal me-1'),
                                                            'Highlight',
                                                        ],
                                                        className='font-size-lg'
                                                    ),
                                                    dbc.Collapse(
                                                        dcc.Checklist(
                                                            options=[
                                                                {
                                                                    'label': html.Span('Main ideas', className='bg-success bg-opacity-50'),
                                                                    'value': 'coresentences'
                                                                },
                                                                {
                                                                    'label': html.Span('Supporting ideas', className='bg-danger bg-opacity-50'),
                                                                    'value': 'extendedcoresentences'
                                                                },
                                                                {
                                                                    'label': html.Span('Argument details', className='bg-warning bg-opacity-50'),
                                                                    'value': 'contentsegments'
                                                                }
                                                            ],
                                                            value=['coresentences'],
                                                            id=show_hide_settings_highlight_checklist,
                                                            labelClassName='form-check nested-form',
                                                            inputClassName='form-check-input'
                                                        ),
                                                        id=show_hide_settings_highlight_collapse,
                                                    )
                                                ],
                                            ),
                                            'value': 'highlight'
                                        },
                                        {
                                            'label': html.Span(
                                                [
                                                    html.Span(
                                                        [
                                                            html.I(className='fas fa-chart-bar me-1'),
                                                            'Indicators overview',
                                                        ],
                                                        className='font-size-lg'
                                                    ),
                                                    dbc.Collapse(
                                                        # TODO need a better way to pull this information from the server
                                                        # currently all options are hardcoded on both sides :P
                                                        dcc.Checklist(
                                                            options=[
                                                                {
                                                                    'label': html.Span(
                                                                        'Transitions',
                                                                        title='Percentile based on total number of transitions used'
                                                                    ),
                                                                    'value': 'transitions'
                                                                },
                                                                {
                                                                    'label': html.Span(
                                                                        'Academic Language',
                                                                        title='Percentile based on percent of academic language used'
                                                                    ),
                                                                    'value': 'academiclanguage'
                                                                },
                                                                {
                                                                    'label': html.Span(
                                                                        'Argument Language',
                                                                        title='Percentile based on percent of argument words used'
                                                                    ),
                                                                    'value': 'argumentlanguage'
                                                                },
                                                                {
                                                                    'label': html.Span(
                                                                        'Attributions',
                                                                        title='Percentile based on total attributes'
                                                                    ),
                                                                    'value': 'attributions'
                                                                },
                                                                {
                                                                    'label': html.Span(
                                                                        'Citations',
                                                                        title='Percentile based on total citations'
                                                                    ),
                                                                    'value': 'cites'
                                                                },
                                                                {
                                                                    'label': html.Span(
                                                                        'Sources',
                                                                        title='Percentile based on total sources'
                                                                    ),
                                                                    'value': 'sources'
                                                                },
                                                            ],
                                                            value=['transitions'],
                                                            id=show_hide_settings_indicator_checklist,
                                                            labelClassName='form-check nested-form',
                                                            inputClassName='form-check-input'
                                                        ),
                                                        id=show_hide_settings_indicator_collapse,
                                                    )
                                                ]
                                            ),
                                            'value': 'indicators'
                                        }
                                    ],
                                    value=['text', 'highlight', 'indicators', 'metrics'],
                                    id=show_hide_settings_checklist,
                                    labelClassName='form-check',
                                    inputClassName='form-check-input'
                                ),
                    ],
                    title='Student Card Options',
                    class_name='rounded-bottom'
                ),
            ],
            active_item=[f'item-{i}' for i in range(2)],
            always_open=True,
            flush=True,
            class_name='border-top'
        ),        
    ],
    id=show_hide_settings_offcanvas,
    # TODO eventually we want sticky-top in the classname however
    # if the screen height is short enough we won't be able to
    # see all options available.
    # need to add overflow to the last accordian item
    class_name='me-2 mb-2'
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='change_sort_direction_icon'),
    Output(sort_icon, 'className'),
    Output(sort_label, 'children'),
    Input(sort_toggle, 'value'),
    Input(sort_by_checklist, 'value')
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='reset_sort_options'),
    Output(sort_by_checklist, 'value'),
    Input(sort_reset, 'n_clicks')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_indicators_checklist'),
    Output(show_hide_settings_indicator_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_metrics_checklist'),
    Output(show_hide_settings_metric_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_text_checklist'),
    Output(show_hide_settings_text_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)

# offcanvas checklist toggle
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='toggle_highlight_checklist'),
    Output(show_hide_settings_highlight_collapse, 'is_open'),
    Input(show_hide_settings_checklist, 'value')
)
