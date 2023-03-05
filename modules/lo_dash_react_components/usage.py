import inspect

import dash.development
from dash import Dash, callback, html, Input, Output

import lo_dash_react_components

test_data = {
    "LOTextHighlight": {
        "id": "text-highlight-test",
        "text": "This is a test of the text highlight component.",
        "highlight_breakpoints": {
            "testHighlight": {
                "id": "testHighlight",
                "value": [
                    [
                        5,
                        7
                    ],
                    [
                        19,
                        28
                    ]
                ],
                "label": "Test Highlight"
            }
        },
        "class_name": "highlight-container"
    }
}

def get_subclasses(module, base_class):
    """Returns a list of all items in a module that are subclasses of `base_class`."""
    return [name for name, obj in inspect.getmembers(module)
            if inspect.isclass(obj) and issubclass(obj, base_class)]

component_list = get_subclasses(lo_dash_react_components, dash.development.base_component.Component)
link_items = [html.Li(html.A(href=f"/components/{component}", children=component)) for component in component_list]
ul = html.Ul(children=link_items)

app = Dash(__name__, use_pages=True, pages_folder="")

for component in component_list:
    path = f"/components/{component}"
    layout = getattr(lo_dash_react_components, component)(**test_data.get(component, {}))
    print(path, layout)
    dash.register_page(component,  path=path, layout=layout)

app.layout = html.Div([
    dash.page_container,
    html.Div(id='output'),
    html.H1("Components"),
    ul
])


if __name__ == '__main__':
    app.run_server(debug=True)
