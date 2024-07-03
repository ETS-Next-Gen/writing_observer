# Dashboards

We can create custom dashboards for the system.

## Dash

Dash is a package for writing and serving web applications directly in Python. In Dash, there are 2 primary items, 1) page components such as headers, divs, spans, etc. and 2) callbacks.

### Getting started

Page components can be set up similar to other `html` layouts, like so

```python
from dash import html

layout = html.Div([
    html.H1(children='This is a header'),
    html.Div(id='A'),
    html.Div(id='B'),
    html.Input(id='input')
])
# html version
# <div>
#     <h1>This is a header</h1>
#     <div id="A"/>
#     <input id="input"/>
# </div>
```

Adding callbacks can introduce interactivity to the dashboard. Dash listens for the value of any `Input` item to change, then runs code and updates the value of the `Output` components. The updated `Output` components could be the `Input` trigger for other callbacks.

```python
from dash import callback, Output, Input

@callback(
    Output('A', 'children'),
    Input('input', 'value')
)
def update_output_children(value):
    '''This callback will trigger whenever the contents of `input`'s `value`
    property changes. It will update the `children` property of `A`.
    '''
    return f'The callback value is: {value}'
```

Callbacks are handled on the server, since we are running Python code. This creates an increase in the network and server resources. Instead, we can use `clientside_callbacks` to run Javascript code on the client's browser.

```python
from dash import clientside_callback, ClientsideFunction, Output, Input

# note this is no longer a decorator, Dash handles adding this code
# to the pages it serves
clientside_callback(
    ClientsideFunction(namespace='my_module', function_name='updateOutputChildren')
    Output('B', 'children'),
    Input('input', 'value')
)
```

```javascript
// `my_module/assets/scripts.js`

// make sure `dash_clientside` is defined first
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

// create a dictionary of functions
window.dash_clientside.my_module = {
    updateOutputChildren: function(value) {
        return `The callback value is: ${value}`
    }
}
```

### Dash in the Learning Observer

The `lo_dash_react_components` offers a variety of components (written in React, ported to Python). This includes a handy websocket component for connecting directly to the communication protocol. We can build components based on the information we receive from the communcation protocol. The protocol may eventually offer partial updates in the future, we so any time we get a new message, we should update a stored object. This stored object should be used to build the components.

```python
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input
import lo_dash_react_components as lodrc

layout = html.Div([
    lodrc.LOConnectionStatusAIO(aio_id=_websocket),
    dcc.Store(id=_websocket_storage),
    html.H2('Output from reducers'),
    html.Div(id=_output)
])

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash')
)

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='receiveWSMessage'),
    Output(_websocket_storage, 'data'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'message'),
    prevent_initial_call=True
)

@callback(
    Output(_output, 'children'),
    Input(_websocket_storage, 'data'),
)
def populate_output(data):
    if not data:
        return 'No students'
    output = [html.Div([
        lodrc.LONameTag(
            profile=s['profile'], className='d-inline-block student-name-tag',
            includeName=True, id=f'{s["user_id"]}-name-tag'
        ),
        html.Span(f' - {s["count"]} events')
    ]) for s in data]
    return output
```

And here are the relevant Javascript functions:

```javascript
window.dash_clientside.learning_observer_template = {
  sendToLOConnection: async function (wsReadyState, urlHash) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update
    }
    if (wsReadyState.readyState === 1) {
      // decode url parameters from hash
      if (urlHash.length === 0) { return window.dash_clientside.no_update }
      const decodedParams = decode_string_dict(urlHash.slice(1))
      if (!decodedParams.course_id) { return window.dash_clientside.no_update }
      // send our request to LO
      const outgoingMessage = {
        learning_observer_template_query: {
          execution_dag: 'learning_observer_template',
          target_exports: ['student_event_counter_export'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  receiveWSMessage: async function (incomingMessage) {
    // parse incoming message
    const messageData = JSON.parse(incomingMessage.data).learning_observer_template_query.student_event_counter_join_roster || [];
    if (messageData.error !== undefined) {
      console.error('Error received from server', messageData.error);
      return [];
    }
    return messageData;
  }
}
```

To add a dashboard to a module, add the following to the module's `module.py` file

```python
# module.py
# ...other definitions
DASH_PAGES = [
    {
        'MODULE': module.path.dash_dashboard,
        'LAYOUT': module.path.dash_dashboard.layout,
        'ASSETS': 'assets',     # define where to find addtional js, css files are
        'TITLE': 'My dashboard title',
        'DESCRIPTION': 'My dashboard description.',
        'SUBPATH': 'my-dashboard-subpath',
        # additional js, css files we want to included
        'CSS': [
            thirdparty_url("css/fontawesome_all.css")
        ],
        'SCRIPTS': [
            static_url("liblo.js")
        ]
    }
]
```
