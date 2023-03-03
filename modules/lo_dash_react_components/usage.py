import lo_dash_react_components
from dash import Dash, callback, html, Input, Output

app = Dash(__name__)

app.layout = html.Div([
    lo_dash_react_components.StudentSelectHeader(
        id='input',
        students=['Bart', 'Nelson', 'Milhouse'],
        selected='Bart'
    ),
    html.Div(id='output')
])


@callback(Output('output', 'children'), Input('input', 'selected'))
def display_output(value):
    return 'You have entered {}'.format(value)


if __name__ == '__main__':
    app.run_server(debug=True)
