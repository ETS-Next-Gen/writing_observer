import asyncio
import collections
import functools
import inspect
import re
import sys


def parse_dot(dot):
    nodes = re.findall(r'(\w+)\s*->\s*(\w+)', dot)
    graph = collections.defaultdict(list)

    for a, b in nodes:
        graph[a].append(b)

    return graph


def build_level_mapping(graph):
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


def create_parent_mapping(graph):
    reversed_graph = {}
    for parent, children in graph.items():
        for child in children:
            if child not in reversed_graph:
                reversed_graph[child] = []
            reversed_graph[child].append(parent)
    return reversed_graph


async def process_pipeline(dot, params, runtime, sd):

    # function_mapping = learning_observer.module_loader.pipeline_functions()
    function_mapping = {
        'A': func_a,
        'B': func_b,
        'C': func_c,
        'D': func_d,
        'E': func_E,
        'F': func_F
    }

    def prep_function_for_pipeline(node, parent_output=None):
        func = function_mapping[node]
        func_params = params.get(node, {})
        args_aggregator = inspect.getfullargspec(func).args

        if parent_output is not None and parent_output != {}:
            # TODO determine how we deal with multiple parent outputs
            print('here', node, ''.join(parent_output.values()))
            func_params.update({'data': ''.join(parent_output.values())})

        if 'runtime' in args_aggregator:
            func_params.update({'runtime': runtime})

        if 'student_data' in args_aggregator:
            func_params.update({'student_data': sd})

        # return async function
        if inspect.iscoroutinefunction(func):
            return func(**func_params)
        # wrap sync function in async
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
  A -> B
  A -> C
  B -> D
  C -> D
  E -> F
"""

parameters = {'A': {'data': 'start_A'}, 'E': {'data': 'start_E'}}

# Run the main function
if __name__ == '__main__':
    output = asyncio.run(process_pipeline(dot_string, parameters, {}, {}))
    print(output)
