# package imports
import dash
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.MINTY, # bootstrap styling
        dbc.icons.FONT_AWESOME, 
    ],
    title='Learning Observer',
    suppress_callback_exceptions=True
)

text = 'The school fair is right around the corner, and tickets have just gone on sale. Even though you may be busy, you will still want to reserve just one day out of an entire year to relax and have fun with us. Even if you don\'t have much money, you don\'t have to worry. A school fair is a community event, and therefore prices are kept low. Perhaps, you are still not convinced. Maybe you feel you are too old for fairs, or you just don\'t like them. Well, that\'s what my grandfather thought, but he came to last year\'s school fair and had this to say about it: "I had the best time of my life!" While it\'s true that you may be able to think of a reason not to come, I\'m also sure that you can think of several reasons why you must come.  We look forward to seeing you at the school fair!'
sentences = text.replace('.', '.\n').split('\n')
highlights = []
for i, sent in enumerate(sentences):
    if i == 0:
        high = 'main'
    elif i == 1 or i == 3:
        high = 'support'
    else:
        high = 'detail'
    comp = html.Span(sent, className=high)
    highlights.append(comp)

# each of these correspond to a css class under assets/highlight.css
tiles = ['highlighted', 'highlight-no-text', 'highlight-thin-text', 'thin-text-no-highlight']

app.layout = dbc.Container(
    dbc.Row(
        [
            dbc.Col(
                highlights,
                md=4,
                lg=3,
                xxl=2,
                class_name=f'{t} border'
            )
            for t in tiles
        ]
    ),
    fluid=True
)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
