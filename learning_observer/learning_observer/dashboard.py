'''
This generates dashboards from student data.
'''

import asyncio
import copy
import inspect
import json
import numbers
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
import learning_observer.rosters as rosters

from learning_observer.log_event import debug_log

import learning_observer.module_loader
import learning_observer.communication_protocol.integration
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.schema
import learning_observer.settings


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
                "user_id": student['user_id'],  # TODO: Encode?
            }

            student_state.update(default_data)

            # TODO/HACK: Only do this for Google data. Make this do the right thing
            # for synthetic data.
            google_id = student['user_id']
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
        roster = [r for r in roster if r['user_id'] == student_id]
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


async def DAGNotFound(dag_name):
    return f'Execution DAG, {dag_name}, not found on system.'


async def DAGIncorrectFormat():
    return 'Submitted Execution DAG not in valid format.'


async def DAGUnsupportedType(t):
    return f'Unsupported type, {t}, for execution_dag parameter.'


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


async def execute_queries(client_data, request):
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
        if learning_observer.settings.settings.get('dangerously_allow_insecure_dags', False) and type(dag) == dict:
            query = dag
            if not learning_observer.communication_protocol.schema.validate_schema(query):
                debug_log(f'Submitted execution query is not a valid form')
                funcs.append(DAGIncorrectFormat())
                continue
        elif type(dag) == str:
            try:
                query = execution_dags[dag]
            except KeyError:
                debug_log(f'Execution DAG, {dag}, not found.')
                funcs.append(DAGNotFound(dag))
                continue
        else:
            debug_log('Unsupported type for execution_dag parameter')
            funcs.append(DAGUnsupportedType(type(dag)))
            continue

        # NOTE dependent dags only work for on a single level dependency
        # TODO allow multiple layers of dependency among dags
        dependent_dags = extract_namespaced_dags(query['execution_dag'])
        missing_dags = dependent_dags - execution_dags.keys()
        if missing_dags:
            debug_log(f'Execution DAGs, {missing_dags}, not found.')
            funcs.append([DAGNotFound(d) for d in missing_dags])
        for dep in dependent_dags:
            dep_dag = copy.deepcopy(execution_dags[dep]['execution_dag'])
            prefixed_dag = fully_qualify_names_with_default_namespace(dep_dag, dep)
            query['execution_dag'] = {**query['execution_dag'], **{f'{dep}.{k}': v for k, v in prefixed_dag.items()}}

        target_exports = client_query.get('target_exports', [])
        query_func = learning_observer.communication_protocol.integration.prepare_dag_execution(query, target_exports)
        client_parameters = client_query.get('kwargs', {})
        runtime = learning_observer.runtime.Runtime(request)
        client_parameters['runtime'] = runtime
        query_func = query_func(**client_parameters)
        funcs.append(query_func)
    return await asyncio.gather(*funcs, return_exceptions=False)


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
    client_data = None

    while True:
        try:
            client_data = await ws.receive_json()
            # TODO we should validate the client_data structure
        except (TypeError, ValueError):
            # these Errors may signal a close
            if (await ws.receive()).type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                return aiohttp.web.Response()
        except asyncio.exceptions.TimeoutError:
            # this is the normal path of the code
            # if the client_data hasn't been set, keep waiting for it
            if client_data is None:
                continue

        if ws.closed:
            debug_log("Socket closed.")
            return aiohttp.web.Response()

        outputs = await execute_queries(client_data, request)

        await ws.send_json({q: v for q, v in zip(client_data.keys(), outputs)})
        # TODO allow the client to set the update timer.
        # it would be cool if the client could set different sleep timers for each item
        await asyncio.sleep(3)


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
