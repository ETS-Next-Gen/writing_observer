'''
This file outputs the text for a flow chart readable by Mermaid.js
Copy the output and paste it here: https://mermaid.live/edit
'''
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.executor


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
    return 'flowchart LR\n' + '\n'.join(subgraphs) + '\n' + '\n'.join(arrows)


if __name__ == '__main__':
    print(create_mermaid_flowchart(learning_observer.communication_protocol.query.EXAMPLE))
