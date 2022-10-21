'''
We plan to use `dash` for most of our dashboards. We are prototyping
integration here.

Right now, we use a common Dash app for all modules. It's likely that we'll want
a Dash app for each module. Dash doesn't give a great way to tease apart things
like static assets, JavaScript files, css, etc. on a per-layout basis.

On the other hand, there's a lot of stuff like `dash.register_page` or global
`client_side_callback`, which seem to presume only one dash app.
'''

import os.path
import shutil

import dash
from dash import Dash, html, clientside_callback, Output, Input

from dash_extensions import WebSocket
import dash_bootstrap_components as dbc
from learning_observer_components import LOConnection

import learning_observer.prestartup
import learning_observer.paths


app = None


def get_app():
    return app


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


def thirdparty_url(filename):
    return "/static/3rd_party/{filename}".format(filename=filename)


test_layout = html.Div(children=[
    html.H1(children='Test Case for Dash'),
    # WebSocket(
    #     id='ws',
    #     url='ws://127.0.0.1:8892/wsapi/dashboard?module=writing_observer&course=12345678901'
    # ),
    LOConnection(
        id='ws',
        data_scope={
	    "module": "writing_observer",
	    "course": 12345
	},
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


def all_dash_style_sheets():
    """
    First, we want to compile together CSS style sheets from modules.
    HACK: These are compiled for all dash pages together, and can
    fight. We will want per-module CSS later. This is good enough
    as scaffolding, though.
    """
    modules = learning_observer.module_loader.dash_pages()
    style_sheets = []
    for module in modules:
        # Pull the CSS out of the modules
        css = sum([m.get('CSS', []) for m in modules[module]], [])
        style_sheets.extend(css)
    return style_sheets


def compile_dash_assets():
    '''
    We want to dump all dash assets into a common directory. Eventually,
    this should be on a per-layout or per-module basis, but again, this
    is good enough for scaffolding.
    '''
    modules = learning_observer.module_loader.dash_pages()

    def asset_paths():
        '''
        Return paths to all the asset directories
        '''
        for m in modules:
            module = modules[m]
            for layout in module:
                if 'ASSETS' in layout:
                    asset_path = os.path.join(layout['_BASE_PATH'], layout['ASSETS'])
                    yield asset_path

    def copy_files(source, destination):
        '''
        Copy all the files, non-recursively, from the source path to the
        destination path. Raise an exception if this would cause a file
        overwrite.
        '''
        for filename in os.listdir(source):
            source_path = os.path.join(source, filename)
            destination_path = os.path.join(destination, filename)
            print("Copying", destination_path)
            if os.path.exists(destination_path):
                raise Exception(f'File {destination_path} already exists compiling Dash assets')
            shutil.copy(source_path, destination_path)

    def delete_files(directory, for_real=False):
        '''
        Delete all the files in a directory.

        To avoid accidental bugs, we have an option to do a dry run,
        enabled by default. We disable once we're confident this is
        doing the right thing, but we'd like to do a dry run by default.

        We don't recurse for now.
        '''
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if for_real:
                print("Removing", file_path)
                os.unlink(file_path)
            else:
                print("Would unlink: {path}".format(path=file_path))

    destination = learning_observer.paths.dash_assets()
    delete_files(destination, for_real=True)
    for source_path in asset_paths():
        copy_files(source_path, destination)

    # Delete all the previous files.
    #
    # In the future, we should only do this if necessary.
    #
    # We don't recurse for now, to avoid dangerous bugs, etc. but this might be
    # a logical thing to consider in the future.
    print(list(asset_paths()))

    return destination


@learning_observer.prestartup.register_startup_check
def load_dash_pages():
    global app
    import learning_observer.module_loader
    modules = learning_observer.module_loader.dash_pages()

    app = Dash(
        __name__,
        use_pages=True,
        pages_folder="",
        external_stylesheets=all_dash_style_sheets(),
        assets_folder=compile_dash_assets(),
        assets_url_path='dash/assets'
    )

    dash.register_page(
        __name__,
        path="/dash/test",
        name="Test Page",
        layout=test_layout
    )

    for module_id in modules:
        for page in modules[module_id]:
            print(module_id)
            path = PATH_TEMPLATE.format(
                module=module_id,
                subpath=page['SUBPATH']
            )

            # TODO: Make an API to do this cleanly.
            page['path'] = path  # <== Bad form. We're breaking abstractions

            local_register_page(
                module=page['MODULE'].__name__,
                layout=page['LAYOUT'],
                title=page['TITLE'],
                description=page['DESCRIPTION'],
                path=path
            )
