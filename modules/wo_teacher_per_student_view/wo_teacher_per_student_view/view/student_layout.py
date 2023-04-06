import dash_bootstrap_components as dbc
import plotly.express

from learning_observer.dash_wrapper import html, dcc
import lo_dash_react_components as lodrc


prefix = 'student-layout'
name = f'{prefix}-name'
highlight = f'{prefix}-highlight-text'
pie_chart = f'{prefix}-pie-chart'

figure = plotly.express.pie(values=[], names=[])
figure.update_traces(textinfo='label+percent')

student_view = html.Div(
    [
        html.H2(id=name),
        lodrc.WOTextHighlight(id=highlight, text='', highlight_breakpoints={}),
        dcc.Graph(id=pie_chart, figure=figure)
    ]
)
