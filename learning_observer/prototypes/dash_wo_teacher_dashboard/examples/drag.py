'''
This file is testing the drag and drop cabilities
'''

#package imports
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ClientsideFunction


app = dash.Dash(
    __name__,
    external_scripts=[
        'https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js',
        'https://epsi95.github.io/dash-draggable-css-scipt/script.js'
    ],
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://epsi95.github.io/dash-draggable-css-scipt/dragula.css'
    ]
)

app.layout = html.Div(id="main", children=[

    html.Div(id="drag_container0", className="container", children=[

        html.Div(id="drag_container", className="container", children=[
            dbc.Card([
                dbc.CardHeader("Card 1"),
                dbc.CardBody(
                    "Some content"
                ),
            ]),
            dbc.Card([
                dbc.CardHeader("Card 2"),
                dbc.CardBody(
                    "Some other content"
                ),
            ]),
            dbc.Card([
                dbc.CardHeader("Card 3"),
                dbc.CardBody(
                    "Some more content"
                ),
            ]),
        ], style={'padding': 10}) ,
            html.Div(id="drag_container2", className="container", children=[
            dbc.Card([
                dbc.CardHeader("Card a"),
                dbc.CardBody(
                    "Some content"
                ),
            ]),
            dbc.Card([
                dbc.CardHeader("Card b"),
                dbc.CardBody(
                    "Some other content"
                ),
            ]),
            dbc.Card([
                dbc.CardHeader("Card c"),
                dbc.CardBody(
                    "Some more content"
                ),
            ]),
        ], style={'padding': 10} )
    ])
])

app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="make_draggable"),
    Output("drag_container0", "data-drag"),
    [Input("drag_container2", "id"),Input("drag_container", "id")]
)

if __name__ == "__main__":
    app.run_server(debug=True)
