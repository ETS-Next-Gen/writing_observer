'''
This is a web interface which provides information about:

* The available queries
* The DAG execution graphs associated with those
* Parameters to said queries
'''

from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_extensions as de
import json

import learning_observer.module_loader
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.executor

main_panel = 'queries-view'
module_store = 'queries-module-store'


def layout():
    queries = learning_observer.module_loader.named_queries()
    modules = {}
    for item in queries.values():
        module = item['module']
        if module in modules:
            modules[module].append(item)
        else:
            modules[module] = [item]

    ret = dbc.Container(
        [
            dcc.Store(id=module_store, data=json.loads(json.dumps(modules, default=lambda x: x.__name__))),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.ListGroup(
                                [
                                    dbc.ListGroupItem(
                                        [
                                            dbc.CardLink(mod, href=f'#{mod}'),
                                            html.Div(
                                                [
                                                    dbc.CardLink(i['name'], class_name='ms-2', href=f'#{i["id"]}')
                                                    for i in modules[mod]
                                                ]
                                            )
                                        ]
                                    ) for mod in modules
                                ]
                            )
                        ),
                        md=4,
                        lg=3
                    ),
                    dbc.Col(
                        dbc.Card(
                            id=main_panel,
                            body=True
                        ),
                        md=8,
                        lg=9
                    )
                ]
            )
        ],
        fluid=True
    )
    return ret


def create_modules(modules):
    row = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardLink(m, href=f'#{m}'),
                    body=True
                ),
                xs=10,
                sm=8,
                md=6,
                lg=4,
                xxl=3
            ) for m in modules
        ],
        justify='around',
        class_name='text-center'
    )
    return row


def create_module(module, items):

    header = [
        html.Thead(html.Tr([html.Th('Name'), html.Th('Description')]))
    ]
    body = [html.Tbody(
        [
            html.Tr(
                [html.Td(dbc.CardLink(i['name'], href=f'#{i["id"]}')), html.Td(i['description'])]
            ) for i in items
        ]
    )]

    div = html.Div(
        [
            html.H4(module),
            dbc.Table(header + body, striped=True)
        ]
    )
    return div


def iteratively_build_flowchart(data, path='', subgraphs=None, arrows=None):
    '''
    Iterate over the execution dag and add pieces of the flowchart as we go.

    :param data: The data dictionary to parse
    :type data: dict
    :param path: The current path in the data structure
    :type path: str
    :param subgraphs: The list of subgraphs
    :type subgraphs: list, optional
    :param arrows: The list of arrows
    :type arrows: list, optional
    :return: A tuple containing the subgraphs and arrows
    :rtype: tuple
    '''
    if subgraphs is None:
        subgraphs = []
    if arrows is None:
        arrows = []
    if isinstance(data, dict):
        if path != '':
            subgraphs.append(f'subgraph {path}')
        for k, v in data.items():
            new_path = f'{path}.{k}' if path else k
            dispatch = k == 'dispatch'
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
                variable_name = data.get('variable_name', None)
                arrows.append(f'{variable_name} --> {path}')
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER:
                parameter_name = data.get('parameter_name', None)
                subgraphs.append(f'{parameter_name}[/Parameter: {parameter_name}/]')
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.CALL:
                parameter_name = data.get('function_name', None)
                subgraphs.append(f'{parameter_name}([Call: {parameter_name}])')
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.MAP:
                parameter_name = data.get('function', None)
                subgraphs.append(f'{parameter_name}[[Map: {parameter_name}]]')
            else:
                iteratively_build_flowchart(v, new_path, subgraphs, arrows)
        if path != '':
            subgraphs.append('end')
    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_path = f'{path}[{i}]'
            iteratively_build_flowchart(v, new_path, subgraphs, arrows)
    return subgraphs, arrows


def create_mermaid_flowchart(endpoint):
    """
    Create a mermaid flowchart from an endpoint.

    :param endpoint: The endpoint dictionary
    :type endpoint: dict
    :return: A string representing the mermaid flowchart
    :rtype: str
    """
    subgraphs, arrows = iteratively_build_flowchart(learning_observer.communication_protocol.executor.flatten(endpoint)['execution_dag'])
    return 'flowchart TD\n' + '\n'.join(subgraphs) + '\n' + '\n'.join(arrows)


def create_parameter(param):
    required = param.get('required', True)
    return html.Div(
        [
            html.H5(
                dcc.Markdown(f'`{param["id"]}`'),
                className='d-inline-block'
            ),
            dbc.Badge('required', class_name='ms-1') if required else html.Span(),
            html.P(
                [
                    html.Strong('Type: '),
                    ' or '.join([str(t.__name__) for t in param['type']]),
                    html.Br(),
                    html.Span(
                        [
                            html.Strong('Default: '),
                            param['default'],
                            html.Br()
                        ]
                    ) if not required else '',
                    html.P(param['description'])
                ]
            ),
        ]
    )


def create_query(item):
    copy = item.copy()
    div = html.Div(
        [
            html.H3(copy['name']),
            dcc.Markdown(copy['description']),
            html.H4('Parameters'),
            html.Div([create_parameter(p) for p in copy['parameters']]),
            html.H4('Output'),
            dcc.Markdown(copy['output']),
            html.H4('Example'),
            dcc.Markdown(f'`{copy["id"]}()`'),
            html.H4('Flow chart'),
            de.Mermaid(
                chart=create_mermaid_flowchart(copy)
            )
        ]
    )
    return div


@callback(
    Output(main_panel, 'children'),
    Input('_pages_location', 'hash'),
    State(module_store, 'data')
)
def update_page(hash, modules):
    if hash is None:
        return create_modules(modules)

    queries = learning_observer.module_loader.named_queries()

    cleaned_hash = hash[1:]
    if cleaned_hash in modules:
        return create_module(cleaned_hash, modules[cleaned_hash])
    elif cleaned_hash in queries:
        return create_query(queries[cleaned_hash])
    else:
        return create_modules(modules)
