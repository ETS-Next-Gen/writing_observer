import asyncio
import collections
import functools
import inspect
import re
import sys


def parse_dot(dot: str) -> dict:
    """
    Parses the given DOT notation and returns a dictionary of nodes and their dependencies.

    :param dot: (str) DOT notation string defining the pipeline of functions and their dependencies.
    :return: (dict) Dictionary containing nodes and their dependencies.
    """
    nodes = re.findall(r'(\w+)\s*->\s*(\w+)', dot)
    graph = collections.defaultdict(list)

    for a, b in nodes:
        graph[a].append(b)

    return graph


def build_level_mapping(graph: dict) -> dict:
    """
    Takes a dictionary of nodes and their dependencies and returns a dictionary of nodes grouped by their level in the dependency tree.

    :param graph: (dict) Dictionary containing nodes and their dependencies.
    :return: (dict) Dictionary containing nodes grouped by their level in the dependency tree.
    """
    levels = {}
    visited = set()

    def traverse(node, level):
        if node in visited:
            return
        visited.add(node)
        if level not in levels:
            levels[level] = []
        levels[level].append(node)
        if node in graph:
            for child in graph[node]:
                traverse(child, level + 1)

    for root in graph:
        traverse(root, 0)

    return levels


def create_parent_mapping(graph: dict) -> dict:
    """
    Takes a dictionary of nodes and their dependencies and returns a dictionary of nodes mapped to their parents.

    :param graph: (dict) Dictionary containing nodes and their dependencies.
    :return: (dict) Dictionary containing nodes mapped to their parents.
    """
    reversed_graph = {}
    for parent, children in graph.items():
        for child in children:
            if child not in reversed_graph:
                reversed_graph[child] = []
            reversed_graph[child].append(parent)
    return reversed_graph


# TODO adjust runtime to expect the runtime object, just hacking so a dict is fine
async def process_pipeline(dot: str, params: dict, runtime: dict, sd: dict) -> dict:
    """
    Processes the pipeline of functions defined by the DOT notation and returns a dictionary of results for each node.

    :param dot: (str) DOT notation string defining the pipeline of functions and their dependencies.
    :param params: (dict) Dictionary containing input parameters for each node in the pipeline.
    :param runtime: (dict) Dictionary containing runtime parameters for the pipeline functions.
    :param sd: (dict) Dictionary containing student data to be used by the pipeline functions.
    :return: (dict) Dictionary containing the output result of each function in the pipeline.
    """

    # TODO fetch the pipeline functions, this is something we will need to create
    # within the module_loader
    # function_mapping = learning_observer.module_loader.pipeline_functions()
    function_mapping = {
        'A': func_a,
        'B': func_b,
        'C': func_c,
        'D': func_d,
        'E': func_E,
        'F': func_F
    }

    def prep_function_for_pipeline(node: str, parent_output: dict = None) -> callable:
        """
        Takes a node and its dependencies, and returns an async function that can be run in the pipeline.

        :param node: (str) Node name to be processed.
        :param parent_output: (dict) Dictionary containing output results from the node's parent nodes.
        :return: (callable) Async function to be run in the pipeline.
        """
        func = function_mapping[node]
        args_aggregator = inspect.getfullargspec(func).args

        # handle adding kwargs to function params
        func_params = params.get(node, {})
        if parent_output is not None and parent_output != {}:
            # TODO determine how we deal with multiple parent outputs
            func_params.update({'data': ''.join(parent_output.values())})

        if 'runtime' in args_aggregator:
            func_params.update({'runtime': runtime})

        if 'student_data' in args_aggregator:
            func_params.update({'student_data': sd})

        # return the function if its async or make it async
        if inspect.iscoroutinefunction(func):
            return func(**func_params)
        partial_func = functools.partial(func, **func_params)
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, partial_func)

    graph = parse_dot(dot)
    node_levels = build_level_mapping(graph)
    parent_mapping = create_parent_mapping(graph)

    results = {}
    for level, nodes in node_levels.items():
        tasks = []
        for node in nodes:
            try:
                prior_results = {parent: results[parent] for parent in parent_mapping.get(node, [])}
                prepped_function = prep_function_for_pipeline(node, prior_results)
                tasks.append(asyncio.create_task(prepped_function))
            except KeyError:
                print(f'Node {node} not found in available pipeline functions.')
                sys.exit()

        # Process nodes at the same level concurrently
        level_results = await asyncio.gather(*tasks)

        # Update the results dictionary
        for node, result in zip(nodes, level_results):
            results[node] = result

    return results


# Define your Python functions
async def func_a(data):
    await asyncio.sleep(1)
    return data + "_A"


async def func_b(data):
    await asyncio.sleep(1)
    return ''.join(data) + "_B"


async def func_c(data):
    await asyncio.sleep(1)
    return ''.join(data) + "_C"


async def func_d(data):
    await asyncio.sleep(1)
    return ''.join(data) + "_D"


async def func_E(data):
    await asyncio.sleep(1)
    return ''.join(data) + "_E"


async def func_F(data):
    await asyncio.sleep(1)
    return ''.join(data) + "_F"


# Map the nodes to the functions
functions = {
    'A': func_a,
    'B': func_b,
    'C': func_c,
    'D': func_d,
    'E': func_E,
    'F': func_F
}

# Define the DOT Notation string
dot_string = """
digraph name {
  A -> B;
  A -> C;
  B -> D;
  C -> D;
  E -> F;
}
"""

parameters = {'A': {'data': 'start_A'}, 'E': {'data': 'start_E'}}

# Run the main function
if __name__ == '__main__':
    output = asyncio.run(process_pipeline(dot_string, parameters, {}, {}))
    print(output)
