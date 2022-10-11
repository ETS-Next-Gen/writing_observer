'''
We plan to use `dash` for most of our dashboards. We are prototyping
integration here.
'''

import dash
from dash import Dash, html, clientside_callback, Output, Input
import learning_observer_components as loc
from dash_extensions import WebSocket
import dash_bootstrap_components as dbc

import learning_observer.prestartup
import os

# We may want to use a separate Dash application per module
app = Dash(
    __name__,
    use_pages=True,
    pages_folder="",
    external_stylesheets=[
        dbc.themes.MINTY,  # bootstrap styling
        dbc.icons.FONT_AWESOME,  # font awesome icons
    ],
    assets_folder=os.path.join(os.getcwd(), 'prototypes/dash_wo_teacher_dashboard/wo_dash/assets/'),
    assets_url_path='dash/assets'
)

# Should we have a namespace for dash than module, or vice-versa?
#
# dash/ makes designing learning observer easier and URL routing, since
# we just add a route for /dash/
#
# {module}/ makes designing apps easier, since they can use relative
# paths.
PATH_TEMPLATE = "/{module}/dash/{subpath}/"


def local_register_page(
    module,
    layout,
    path,
    title,
    description
):
    dash.register_page(
        module,
        layout=layout,
        title=title,
        description=description,
        path=path
    )


test_layout = html.Div(children=[
    html.H1(children='Test Case for Dash'),
    loc.WebSocket(
        id='ws',
        url='ws://10.1.0.224:8888/wsapi/dashboard?module=writing_observer&course=12345678901'
    ),
    html.Div(id='output')
])

clientside_callback(
    """function(msg) {
        if(!msg) {
            return "No Data"
        }
        return msg.data;
    } """,
    Output('output', 'children'),
    Input('ws', 'message')
)


dash.register_page(
    __name__,
    path="/dash/test",
    name="Test Page",
    layout=test_layout
)


@learning_observer.prestartup.register_startup_check
def load_dash_pages():
    import learning_observer.module_loader
    modules = learning_observer.module_loader.dash_pages()
    for module_id in modules:
        for page in modules[module_id]:
            print(module_id)
            path = PATH_TEMPLATE.format(
                    module=module_id,
                    subpath=page['SUBPATH']
            )

            page['path'] = path  # <== Bad form. We're breaking abstractions
                                 # TODO: Make an API to do this cleanly.

            local_register_page(
                module=page['MODULE'].__name__,
                layout=page['LAYOUT'],
                title=page['TITLE'],
                description=page['DESCRIPTION'],
                path=path
            )
