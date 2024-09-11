'''
This generates dashboards from student data.
'''

import asyncio
import copy
import inspect
import json
import jsonschema
import numbers
import pmss
import queue
import time

import aiohttp

import learning_observer.util as util

import learning_observer.synthetic_student_data as synthetic_student_data

import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.kvs as kvs
import learning_observer.runtime

import learning_observer.paths as paths

import learning_observer.auth
import learning_observer.constants as constants
import learning_observer.rosters as rosters

from learning_observer.log_event import debug_log

import learning_observer.module_loader
import learning_observer.communication_protocol.integration
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.schema
import learning_observer.settings

pmss.register_field(
    name='dangerously_allow_insecure_dags',
    type=pmss.pmsstypes.TYPES.boolean,
    description='Data can be queried either by system defined execution DAGs '\
                '(directed acyclic graphs) or user created execution DAGs. '\
                'This is useful for developing new system queries, but should not '\
                'be used in production.',
    default=False
)


def timelist_to_seconds(timelist):
    '''
    [5, "seconds"] ==> 5
    [5, "minutes"] ==> 300
    etc.
    '''
    if timelist is None:
        return None
    if len(timelist) != 2:
        raise Exception("Time lists should have number and units")
    if not isinstance(timelist[0], numbers.Number):
        raise Exception("First element should be a number")
    if not isinstance(timelist[1], str):
        raise Exception("Second element should be a string")
    units = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600
    }
    if timelist[1] not in units:
        raise Exception("Second element should be a time unit")
    return timelist[0] * units[timelist[1]]


@learning_observer.auth.teacher
async def generic_dashboard(request):
    '''
    We would like to be able to support pretty arbitrary dashboards,
    where the client asks for a subset of data and we send it.

    This is probably the wrong abstraction, but our goal is to allows
    arbitrary dashboards client-side.

    We're figuring out what we're doing. This view is behind a feature
    flag, since we have no clear idea.

    Our goal is to be able to set up appropriate queries to deliver
    pretty generic aggregations.

    The current model has the client ask for specific data, and for us
    to send it back. However, the concept of doing this more server-side
    makes a lot of sense too.

    GraphQL looks super-relevant. Implementing it is a big lift, and
    it might need to be slightly adapted to the context.

    The test case for this is in `util/generic_websocket_dashboard.py`
    '''
    # We never send data more than twice per second, because performance.
    MIN_REFRESH = 0.5

    teacherkvs = kvs.KVS()
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    subscriptions = queue.PriorityQueue()

    def timeout():
        '''
        Calculate the time until we need to send the next message.
        '''
        if subscriptions.empty():
            return None
        else:
            Δt = subscriptions.queue[0][0] - time.time()
            return Δt

    count = [0]

    def counter():
        count[0] += 1
        return count[0]

    running = False           # Are we streaming data?
    next_subscription = None  # What is the next item to send?

    while True:
        # Wait for the next message, with an upper bound of when we
        # need to get back to the client.
        try:
            if subscriptions.empty() or not running:
                msg = await ws.receive()
            else:
                msg = await ws.receive(timeout=timeout())
            debug_log("msg", msg)
            if msg.type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                # By this point, the client is long gone, but we want to
                # return something to avoid confusing middlewares.
                return aiohttp.web.Response(text="This never makes it back....")
            elif msg.type == aiohttp.WSMsgType.TEXT:
                message = json.loads(msg.data)
                debug_log(message)
                if message['action'] == 'subscribe':
                    subscriptions.put([
                        time.time(),
                        {
                            'keys': message['keys'],
                            'ids': [sa_helpers.make_key_from_json(key) for key in message['keys']],
                            'refresh': timelist_to_seconds(message['refresh']),
                            'subscription_id': message.get('subscription_id', counter())
                        }
                    ])
                elif message['action'] == 'start':
                    await ws.send_json(
                        {'subscribed': [i[1] for i in subscriptions.queue]}
                    )
                    running = True
                elif message['action'] == 'hangup':
                    break
        # If we didn't get a message before we need to send one,
        # just keep going.
        except asyncio.exceptions.TimeoutError:
            pass
        if ws.closed:
            debug_log("Socket closed")
            return aiohttp.web.Response(text="This never makes it back to the client....")
        # Now, we send any messages we need to
        while timeout() is not None and timeout() < 0:
            response = {}
            t, s = subscriptions.get()
            for key, json_key in zip(s['ids'], s['keys']):
                response[key] = await teacherkvs[key]
                if isinstance(response[key], dict):
                    response[key]['key'] = json_key
            response['subscription_id'] = s['subscription_id']
            if 'refresh' in s and s['refresh'] is not None:
                subscriptions.put([time.time() + max(s['refresh'], MIN_REFRESH), s])
            await ws.send_json(response)

    return aiohttp.web.Response(text="This should never happen....")


def fetch_student_state(
        course_id, module_id,
        agg_module, roster,
        default_data={}
):
    '''
    This closure will compile student data from a roster of students.

    Closure remembers course roster, and redis KVS.

    Reopening connections to redis every few seconds otherwise would
    run us out of file pointers.
    '''
    teacherkvs = kvs.KVS()

    async def student_state_fetcher():
        '''
        Poll redis for student state. This should be abstracted out into a
        generic aggregator API, much like we have a reducer on the
        incoming end.
        '''
        students = []
        for student in roster:
            student_state = {
                # We're copying Google's roster format here.
                #
                # It's imperfect, and we may want to change it later, but it seems
                # better than reinventing our own standard.
                #
                # We don't copy verbatim, since we do want to filter down any
                # extra stuff.
                'profile': {
                    'name': {
                        'full_name': student['profile']['name']['full_name']
                    },
                    'photo_url': student['profile'].get('photo_url', ''),
                    'email_address': student['profile'].get('email_address', ''),
                    'external_ids': student['profile'].get('external_ids', []),
                },
                "course_id": course_id,
                constants.USER_ID: student[constants.USER_ID],  # TODO: Encode?
            }

            student_state.update(default_data)

            # TODO/HACK: Only do this for Google data. Make this do the right thing
            # for synthetic data.
            google_id = student[constants.USER_ID]
            if google_id.isnumeric():
                student_id = learning_observer.auth.google_id_to_user_id(google_id)
            else:
                student_id = google_id
            # TODO: Evaluate whether this is a bottleneck.
            #
            # mget is faster than ~50 gets. But some online benchmarks show both taking
            # microseconds, to where it might not matter.
            #
            # For most services (e.g. a SQL database), this would be a huge bottleneck. redis might
            # be fast enough that it doesn't matter? Dunno.
            for sa_module in agg_module['sources']:
                key = sa_helpers.make_key(
                    sa_module,
                    {sa_helpers.KeyField.STUDENT: student_id},
                    sa_helpers.KeyStateType.EXTERNAL)
                data = await teacherkvs[key]
                # debug_log(key, data)  # <-- Useful, but a lot of stuff is spit out.
                if data is not None:
                    student_state[sa_helpers.fully_qualified_function_name(sa_module)] = data
            cleaner = agg_module.get("cleaner", lambda x: x)
            students.append(cleaner(student_state))

        return students
    return student_state_fetcher


def find_course_aggregator(module_id):
    '''
    Find a course aggregator based on a `module_id`

    * This should move to the modules package.
    * We should support having a list of these
    '''
    course_aggregator_module = None
    default_data = {}
    course_aggregator_candidates = learning_observer.module_loader.course_aggregators()
    for candidate_module in course_aggregator_candidates:
        if course_aggregator_candidates[candidate_module]['short_id'] == module_id:
            # TODO: We should support multiple modules here.
            if course_aggregator_module is not None:
                raise aiohttp.web.HTTPNotImplemented(text="Duplicate module: " + candidate_module)
            course_aggregator_module = course_aggregator_candidates[candidate_module]
            default_data = course_aggregator_module.get('default-data', {})
    return (course_aggregator_module, default_data)


@learning_observer.auth.teacher
async def websocket_dashboard_view(request):
    '''
    Handler to aggregate student data, and serve it back to the client
    every half-second to second or so.

    TODO remove this method. This is the old way of passing data from
    the server to the client (pre communication protocol).
    '''
    # Extract parameters from the URL
    #
    # Note that we need to do auth/auth. At present, we always want a
    # course ID, even for a single student. If a teacher requests a
    # students' data, we want to make sure that sutdnet is in that
    # teacher's course.
    course_id = request.rel_url.query.get("course")
    # module_id should support a list, perhaps?
    module_id = request.rel_url.query.get("module")
    # For student dashboards
    student_id = request.rel_url.query.get("student", None)
    # For individual resources
    resource_id = request.rel_url.query.get("resource", None)
    # How often do we refresh? Default is 0.5 seconds
    refresh = 0.5  # request.match_info.get('refresh', 0.5)

    # Find the right module
    course_aggregator_module, default_data = find_course_aggregator(module_id)

    if course_aggregator_module is None:
        debug_log("Bad module: ", module_id)
        available = learning_observer.module_loader.course_aggregators()
        debug_log("Available modules: ", [available[key]['short_id'] for key in available])
        raise aiohttp.web.HTTPBadRequest(text="Invalid module: {}".format(module_id))

    # We need to receive to detect web socket closures.
    ws = aiohttp.web.WebSocketResponse(receive_timeout=0.1)
    await ws.prepare(request)

    roster = await rosters.courseroster(request, course_id)

    # If we're grabbing data for just one student, we filter the
    # roster down.  This pathway ensures we only serve data for
    # students on a class roster.  I'm not sure this API is
    # right. Should we have a different URL? A set of filters? A lot
    # of that is TBD. Once nice property about this is that we have
    # the same data format for 1 student as for a classroom of
    # students.
    if student_id is not None:
        roster = [r for r in roster if r[constants.USER_ID] == student_id]
    # Grab student list, and deliver to the client
    student_state_fetcher = fetch_student_state(
        course_id,
        module_id,
        course_aggregator_module,
        roster,
        default_data
    )
    aggregator = course_aggregator_module.get('aggregator', lambda x: {})
    async_aggregator = inspect.iscoroutinefunction(aggregator)
    args_aggregrator = inspect.getfullargspec(aggregator)[0]
    client_data = None
    runtime = learning_observer.runtime.Runtime(request)

    while True:
        sd = await student_state_fetcher()
        data = {
            "student_data": sd   # Per-student list
        }
        # Prep the aggregator function to be called.
        # Determine if we should pass the client_data in or not/async capability
        # Currently options is a list of strings (what we want returned)
        # In the futuer this should be some form of communication protocol
        if 'options' in args_aggregrator:
            agg = aggregator(runtime, sd, client_data)
        else:
            agg = aggregator(runtime, sd)
        if async_aggregator:
            agg = await agg
        data.update(agg)
        await ws.send_json(data)
        # First try to receive a json, if you receive something that can't be json'd
        # check for closing, otherwise timeout will fire
        # This is kind of an awkward block, but aiohttp doesn't detect
        # when sockets close unless they receive data. We try to receive,
        # and wait for an exception or a CLOSE message.
        try:
            client_data = await ws.receive_json()
        except (TypeError, ValueError):
            if (await ws.receive()).type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                # By this point, the client is long gone, but we want to
                # return something to avoid confusing middlewares.
                return aiohttp.web.Response(text="This never makes it back....")
        except asyncio.exceptions.TimeoutError:
            # This is the normal code path
            pass
        await asyncio.sleep(0.5)
        # This never gets called, since we return above
        if ws.closed:
            debug_log("Socket closed. This should never appear, however.")
            return aiohttp.web.Response(text="This never makes it back....")


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


# TODO both of these require us to pass in a list of functions
# this was the old way of doing this, we ought to change this
DAG_DISPATCH = {dict: dispatch_defined_execution_dag, str: dispatch_named_execution_dag}


async def execute_queries(client_data, request):
    '''TODO remove this method as it is no longer used.
    '''
    execution_dags = learning_observer.module_loader.execution_dags()
    funcs = []
    # client_data = {
    #     'output_name': {
    #         'execution_dag': 'writing_obssdfsderver',
    #         'target_exports': ['docs_with_roster'],
    #         'kwargs': {'course_id': 12345}
    #     },
    # }
    for query_name, client_query in client_data.items():
        dag = client_query.get('execution_dag', query_name)

        if type(dag) not in DAG_DISPATCH:
            debug_log(await dag_unsupported_type(type(dag)))
            funcs.append(dag_unsupported_type(type(dag)))
            continue

        query = await DAG_DISPATCH[type(dag)](dag, funcs)
        if query is None:
            continue

        # NOTE dependent dags only work for on a single level dependency
        # TODO allow multiple layers of dependency among dags
        dependent_dags = extract_namespaced_dags(query['execution_dag'])
        missing_dags = dependent_dags - execution_dags.keys()
        if missing_dags:
            debug_log(await dag_not_found(missing_dags))
            funcs.append(dag_not_found(missing_dags))
            continue
        for dep in dependent_dags:
            dep_dag = copy.deepcopy(execution_dags[dep]['execution_dag'])
            prefixed_dag = fully_qualify_names_with_default_namespace(dep_dag, dep)
            query['execution_dag'] = {**query['execution_dag'], **{f'{dep}.{k}': v for k, v in prefixed_dag.items()}}

        target_exports = client_query.get('target_exports', [])
        query_func = learning_observer.communication_protocol.integration.prepare_dag_execution(query, target_exports)
        client_parameters = client_query.get('kwargs', {}).copy()
        runtime = learning_observer.runtime.Runtime(request)
        client_parameters['runtime'] = runtime
        query_func = query_func(**client_parameters)
        funcs.append(query_func)
    return await asyncio.gather(*funcs, return_exceptions=False)


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
            output.append(provenance['STUDENT']['user_id'])
        if 'RESOURCE' in provenance:
            output.append('documents')
            output.append(provenance['RESOURCE']['doc_id'])
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
        generator = await _create_dag_generator(dag_query, target, request)
        await _drive_generator(generator, dag_query['kwargs'])
        # TODO pull this from kwargs if available
        await asyncio.sleep(10)
        await _execute_dag(dag_query, target, params)

    async def _drive_generator(generator, dag_kwargs):
        '''For each item in the generator, this method creates
        an update to send to the client.
        '''
        async for item in generator:
            scope = _find_student_or_resource(item)
            update_path = ".".join(scope)
            if 'option_hash' in dag_kwargs:
                item['option_hash'] = dag_kwargs['option_hash']
            await _send_update({'op': 'update', 'path': update_path, 'value': item})

    send_batches = asyncio.create_task(_batch_send())

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
                    asyncio.create_task(_execute_dag(v, target, client_query))


# Obsolete code -- we should put this back in after our refactor. Allows us to use
# dummy data
# @learning_observer.auth.teacher
# async def static_student_data_handler(request):
#     '''
#     Populate static / mock-up dashboard with static fake data
#     '''
#     # module_id = request.match_info['module_id']
#     # course_id = int(request.match_info['course_id'])

#     return aiohttp.web.json_response({
#         "new_student_data": json.load(open(paths.static("student_data.js")))
#     })


# @learning_observer.auth.teacher
# async def generated_student_data_handler(request):
#     '''
#     Populate static / mock-up dashboard with static fake data dynamically
#     '''
#     # module_id = request.match_info['module_id']
#     # course_id = int(request.match_info['course_id'])

#     return aiohttp.web.json_response({
#         "new_student_data": synthetic_student_data.synthetic_data()
#     })
