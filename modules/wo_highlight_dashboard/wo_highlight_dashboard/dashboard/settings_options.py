'''
Defines the options in the settings panel
'''
# package imports
from dash import html
import dash_bootstrap_components as dbc


def create_metric_label(opt, child=False):
    return dbc.Badge(
        opt.get('name'),
        color='info',
        title=opt.get('tooltip', ''),
        class_name='subchecklist-label' if child else ''
    )


def create_highlight_label(opt, child=False):
    class_name = f"{opt.get('id')}_highlight"
    return html.Span(
        opt.get('name'),
        title=opt.get('tooltip', ''),
        className=f'subchecklist-label {class_name}' if child else class_name
    )


def create_generic_label(opt, child=False):
    return html.Span(
        opt.get('name'),
        title=opt.get('tooltip', ''),
        className='subchecklist-label' if child else ''
    )


def create_checklist_options(user_options, options, selector_type):
    if selector_type == 'metric':
        label_maker = create_metric_label
    elif selector_type == 'highlight':
        label_maker = create_highlight_label
    else:
        label_maker = create_generic_label
    ui_options = []
    for opt_id in user_options:
        opt = next((o for o in options if o['id'] == opt_id), None)
        if opt is None:
            children = [o for o in options if o['parent'] == opt_id]
            children_options = [
                {
                    'label': label_maker(child, child=True),
                    'value': child['id']
                } for child in children
            ]
            ui_options.append({'label': opt_id, 'value': opt_id, 'disabled': True})
            ui_options.extend(children_options)
        else:
            ui_options.append({
                'label': label_maker(opt),
                'value': opt['id']
            })
    return ui_options
