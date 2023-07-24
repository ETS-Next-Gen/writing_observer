import dash_bootstrap_components as dbc


prefix = 'student-activity'
inactive = f'{prefix}-inactive'
active = f'{prefix}-active'


def create_activity_card(id, title):
    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody(dbc.Row(id=id, class_name='g-1 student-activity-status-row'))
        ]),
        sm=6
    )


def student_activity():
    inactive_card = create_activity_card(inactive, 'Inactive')
    active_card = create_activity_card(active, 'Active')
    row = dbc.Row([
        inactive_card,
        active_card
    ], class_name='g-1')
    return row
