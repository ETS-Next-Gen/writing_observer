'''
This generates dashboards from student data.
'''

import aiohttp
import aiohttp.client_exceptions
import asyncio
import copy
import jsonschema
import pmss

import learning_observer.auth
import learning_observer.communication_protocol.integration
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.schema
import learning_observer.module_loader
import learning_observer.runtime
import learning_observer.settings

from learning_observer.log_event import debug_log


pmss.register_field(
    name='dangerously_allow_insecure_dags',
    type=pmss.pmsstypes.TYPES.boolean,
    description='Data can be queried either by system defined execution DAGs '\
                '(directed acyclic graphs) or user created execution DAGs. '\
                'This is useful for developing new system queries, but should not '\
                'be used in production.',
    default=False
)


# We use following functions to return an error message about the requested
# DAG back to the user.
async def dag_not_found(dags):
    if type(dags) == set:
        return f'Execution DAG{"s" if len(dags) > 1 else ""}, {", ".join(dags)}, not found on system.'
    return f'Execution DAG, {dags}, not found on system.'


async def dag_incorrect_format(e):
    return f'Submitted Execution DAG not in valid format: {e}'


async def dag_unsupported_type(t):
    return f'Unsupported type, {t}, for execution_dag parameter.'


async def dag_submission_not_allowed():
    return 'Submitting fully formed DAGs is not supported.'


def extract_namespaced_dags(dag, deps=None):
    '''This will return any dependencies on other dags
    (in other words, variables of the form namespace.variable which are not local).
    If it finds something like writing_observer.docs, it will add that to a set,
    and return that set of dependencies.

    This is so we can have a complete list of DAG nodes we might need to reference.
    We can take the keys from the execution_dag dictionary, but we also add all of
    the references to DAGs in other modules.
    '''
    # TODO move this function to the communication protocol directory
    if deps is None:
        deps = set()

    if isinstance(dag, dict):
        if dag.get('dispatch') == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
            variable_name = dag['variable_name']
            if '.' in variable_name:
                deps.add(variable_name.split('.')[0])
        for key in dag:
            extract_namespaced_dags(dag[key], deps)
    return deps


def fully_qualify_names_with_default_namespace(dag, namespace_prefix):
    '''In order to avoid naming conflicts, and to have consistency, this will append
    the default namespace to all variables without a namespace prefix.

    For example, if the prefix is writing_observer, and we run into a node `docs`,
    this node will be renamed to `writing_observer.docs`.

    TODO If a node already has a prefix (e.g. dynamic_assessment.foo), it will remain unchanged.
    '''
    # TODO move this function to the communication protocol directory
    if isinstance(dag, dict):
        if dag.get('dispatch') == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
            dag['variable_name'] = f'{namespace_prefix}.{dag["variable_name"]}'
        for key in dag:
            fully_qualify_names_with_default_namespace(dag[key], namespace_prefix)
    return dag


async def dispatch_named_execution_dag(dag_name):
    '''This method takes a Named Query and fetches it from the
    available DAGs on the system.
    '''
    available_dags = learning_observer.module_loader.execution_dags()
    query = None
    try:
        query = available_dags[dag_name]
    except KeyError:
        debug_log(await dag_not_found(dag_name))
    finally:
        return query


async def dispatch_defined_execution_dag(dag):
    '''This method confirms that an Open Queries provided by the user
    are 1) allowed to be submitted and 2) adhere to the appropriate
    JSON structure.
    '''
    query = None
    if not learning_observer.settings.pmss_settings.dangerously_allow_insecure_dags():
        debug_log(await dag_submission_not_allowed())
        return query
    try:
        learning_observer.communication_protocol.schema.prevalidate_schema(dag)
        query = dag
    except jsonschema.ValidationError as e:
        debug_log(await dag_incorrect_format(e))
        return query
    finally:
        return query


DAG_DISPATCH = {dict: dispatch_defined_execution_dag, str: dispatch_named_execution_dag}


async def _handle_dependent_dags(query):
    '''
    Handles dependent DAGs and ensures all dependencies are present.
    NOTE dependent dags only work for on a single level dependency
    TODO allow multiple layers of dependency among dags
    '''
    execution_dags = learning_observer.module_loader.execution_dags()
    dependent_dags = extract_namespaced_dags(query['execution_dag'])
    missing_dags = dependent_dags - execution_dags.keys()

    if missing_dags:
        # TODO we ought to handle this as an error
        debug_log(await dag_not_found(missing_dags))
        return

    for dep in dependent_dags:
        # Copy and qualify names for dependent DAG
        dep_dag = copy.deepcopy(execution_dags[dep]['execution_dag'])
        prefixed_dag = fully_qualify_names_with_default_namespace(dep_dag, dep)

        # Merge dependent DAG with current query
        query['execution_dag'] = {**query['execution_dag'], **{f'{dep}.{k}': v for k, v in prefixed_dag.items()}}

    return query


async def _prepare_dag_as_generator(client_query, query, target, request):
    '''
    Prepares the query for execution, sets up client parameters and runtime.
    '''
    target_exports = [target]

    # Prepare the DAG execution function
    query_func = learning_observer.communication_protocol.integration.prepare_dag_execution(query, target_exports)

    # Handle client parameters and runtime setup
    client_parameters = client_query.get('kwargs', {}).copy()
    runtime = learning_observer.runtime.Runtime(request)
    client_parameters['runtime'] = runtime

    # Execute the query and return the first value from the generator
    generator_dictionary = await query_func(**client_parameters)
    return next(iter(generator_dictionary.values()))


async def _create_dag_generator(client_query, target, request):
    dag = client_query['execution_dag']
    if type(dag) not in DAG_DISPATCH:
        debug_log(await dag_unsupported_type(type(dag)))
        return

    query = await DAG_DISPATCH[type(dag)](dag)
    if query is None:
        # the DAG_DISPATCH prints a more detailed message about why
        debug_log('The submitted query failed.')
        return
    query = await _handle_dependent_dags(query)
    return await _prepare_dag_as_generator(client_query, query, target, request)


def _find_student_or_resource(d):
    '''HACK the communication protocol does not provide an easy way to
    determine which student or student/document pair is being updated.
    The protocol does include a provenance key with each item that includes
    the history of what occured within the protocol.
    In production settings, the provenance should be removed from the
    user output. However, this method assumes that the provenance is still
    around.
    This method digs into the provenance and extracts the corresponding
    student or student/document id. This information is used to tell the
    client which items in their data-tree to update (i.e. update Billy's
    History Essay with this new information).
    '''
    if not isinstance(d, dict):
        return []
    if 'provenance' in d:
        provenance = d['provenance']
        output = []
        if 'STUDENT' in provenance:
            output.append('students')
            output.append(provenance['STUDENT']['user_id'])
        if 'RESOURCE' in provenance:
            if 'doc_id' in provenance['RESOURCE']:
                output.append('documents')
                output.append(provenance['RESOURCE']['doc_id'])
            if 'assignment_id' in provenance['RESOURCE']:
                output.append('assignments')
                output.append(provenance['RESOURCE']['assignment_id'])
        if output:
            return output
        return _find_student_or_resource(provenance)
    return []


@learning_observer.auth.teacher
async def websocket_dashboard_handler(request):
    '''
    Handles client requests through a WebSocket, executes requested queries,
    and sends back the results.

    Args:
        request: aiohttp request object.

    Returns:
        aiohttp web response.
    '''
    ws = aiohttp.web.WebSocketResponse(receive_timeout=0.3)
    await ws.prepare(request)
    client_query = None
    previous_client_query = None
    batch = []
    lock = asyncio.Lock()
    background_tasks = set()

    async def _send_update(update):
        '''Send an update to our batch
        '''
        async with lock:
            batch.append(update)

    async def _batch_send():
        '''If our batch has any items, send them to the client
        then wait before checking again.
        '''
        while True:
            async with lock:
                if batch:
                    try:
                        await ws.send_json(batch)
                        batch.clear()
                    except aiohttp.web_ws.WebSocketError:
                        break
                    except aiohttp.client_exceptions.ClientConnectionResetError:
                        break
            if ws.closed:
                break
            # TODO this ought to be pulled from somewhere
            await asyncio.sleep(1)

    async def _execute_dag(dag_query, target, params):
        '''This method creates the DAG generator and drives it.
        Once finished, we wait until rescheduling it. If the parameters
        change, we exit before creating and driving the generator.
        '''
        if params != client_query:
            # the params are different and we should stop this generator
            return

        # Create DAG generator and drive
        generator = await _create_dag_generator(dag_query, target, request)
        await _drive_generator(generator, dag_query['kwargs'], target=target)

        # Handle rescheduling the execution of the DAG for fresh data
        # TODO add some way to specific specific endpoint delays
        dag_delay = dag_query['kwargs'].get('rerun_dag_delay', 10)
        if dag_delay < 0:
            # if dag_delay is negative, we skip repeated execution
            return
        await asyncio.sleep(dag_delay)
        await _execute_dag(dag_query, target, params)

    async def _drive_generator(generator, dag_kwargs, target=None):
        '''For each item in the generator, this method creates
        an update to send to the client.
        '''
        async for item in generator:
            scope = _find_student_or_resource(item)
            update_path = ".".join(scope)
            if 'option_hash' in dag_kwargs and target is not None:
                item[f'option_hash_{target}'] = dag_kwargs['option_hash']
            await _send_update({'op': 'update', 'path': update_path, 'value': item})

    send_batches_task = asyncio.create_task(_batch_send())
    background_tasks.add(send_batches_task)
    send_batches_task.add_done_callback(background_tasks.discard)

    while True:
        try:
            received_params = await ws.receive_json()
            client_query = received_params
            # TODO we should validate the client_query structure
        except (TypeError, ValueError):
            # these Errors may signal a close
            if (await ws.receive()).type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                return aiohttp.web.Response()
        except asyncio.exceptions.TimeoutError:
            # this is the normal path of the code
            # if the client_query hasn't been set, keep waiting for it
            if client_query is None:
                continue

        if ws.closed:
            debug_log("Socket closed.")
            return aiohttp.web.Response()

        if client_query != previous_client_query:
            previous_client_query = copy.deepcopy(client_query)
            # HACK even though we can specificy multiple targets for a
            # single DAG, this creates a new DAG for each. This eventually
            # allows us to specify different parameters (such as the
            # reschedule timeout).
            for k, v in client_query.items():
                for target in v.get('target_exports', []):
                    execute_dag_task = asyncio.create_task(_execute_dag(v, target, client_query))
                    background_tasks.add(execute_dag_task)
                    execute_dag_task.add_done_callback(background_tasks.discard)
