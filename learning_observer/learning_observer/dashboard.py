'''
This generates dashboards from student data.
'''

import aiohttp
import asyncio
import inspect
import json
import jsonschema
import numbers
import queue
import time

import learning_observer.auth
import learning_observer.communication_protocol
import learning_observer.kvs as kvs
from learning_observer.log_event import debug_log
import learning_observer.module_loader
import learning_observer.rosters as rosters
import learning_observer.runtime
import learning_observer.settings
import learning_observer.stream_analytics.helpers as sa_helpers


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
                # debug_log(data) <-- Useful, but a lot of stuff is spit out.
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

    client_data_schema = course_aggregator_module.get('client_data', learning_observer.communication_protocol.base_schema)

    while True:
        sd = await student_state_fetcher()
        data = {
            "student_data": sd   # Per-student list
        }
        # Prep the aggregator function to be called.
        # Determine if we should pass the client_data in or not/async capability
        # Currently options is a list of strings (what we want returned)
        # In the futuer this should be some form of communication protocol
        if 'client_data' in args_aggregrator:
            agg = aggregator(runtime, sd, client_data)
        else:
            agg = aggregator(runtime, sd)
        if async_aggregator:
            agg = await agg
        data.update(agg)
        await ws.send_json(data)
        # First try to receive a json,
        # then validate it against the current module's client data schema
        # if you receive something that can't be json'd
        # check for closing, otherwise timeout will fire
        # This is kind of an awkward block, but aiohttp doesn't detect
        # when sockets close unless they receive data. We try to receive,
        # and wait for an exception or a CLOSE message.
        try:
            client_data = await ws.receive_json()
            jsonschema.validate(client_data, client_data_schema)
        except jsonschema.ValidationError as e:
            debug_log('Something is wrong with the data received from the client:\n', e)
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


async def process_function(func, parameters, runtime, sd):
    """
    Process a function or a list of functions and/or nested lists of functions.
    Passes the output from one function to the next as the 'prev_output' parameter.

    :param func: A function or a list of functions and/or nested lists of functions.
    :param parameters: A dictionary of key-value pairs to pass into each function
    :param runtime: The runtime object.
    :param sd: The student_data object.
    :return: A dictionary with the final output of the functions.

    Example 1 - func is a function:
    ```python
    # inputs
    func = add
    parameters = {'x': 1, 'y': 2}
    # add 1 and 2 together
    output = process_function(func, parameters, runtime, sd)
    # 3
    ```

    Example 2 - func is a list:
    ```python
    # inputs
    func = [sub, [mult, double]]
    # should be same nested list structure as the func
    # subtract 4 from 3, multiply that by 2, then double it
    parameters = [{'x': 3, 'y': 4}, [{y: 2}, {}]]
    output = process_function(func, paramters, runtime, sd)
    # -4
    ```
    """
    async def execute_async_function(func, **params):
        """
        Execute a function and await the result if it's asynchronous.

        :param func: The function to execute.
        :param params: The parameters to pass to the function.
        :return: The result of the function execution.
        """
        result = func(**params)
        if inspect.iscoroutinefunction(func):
            result = await result
        return result

    async def process_nested_function(func, params, prev_output=None):
        """
        Process a function or a list of functions and/or nested lists of functions.
        Passes the output from one function to the next as the 'prev_output' parameter.

        :param func: A function or a list of functions and/or nested lists of functions.
        :param params: A dictionary or list of parameters for the functions.
        :param prev_output: The output from the previous function.
        :return: The final output of the functions.
        """
        if callable(func):
            functions = [func]
        elif isinstance(func, list):
            functions = func
        else:
            raise ValueError("Invalid 'func' argument. Must be a callable or a list of callables.")

        for idx, func in enumerate(functions):
            if isinstance(func, list):
                nested_params = params[idx] if isinstance(params, list) and len(params) > idx else None
                prev_output = await process_nested_function(func, nested_params, prev_output)
                continue

            args_aggregator = inspect.getfullargspec(func).args

            func_params = params[idx] if isinstance(params, list) and len(params) > idx else params

            if 'runtime' in args_aggregator:
                func_params.update({'runtime': runtime})

            if 'student_data' in args_aggregator:
                func_params.update({'student_data': sd})

            if prev_output and 'prev_output' in args_aggregator:
                func_params.update({'prev_output': prev_output})
            agg = await execute_async_function(func, **func_params)

            prev_output = agg

        return prev_output

    final_output = await process_nested_function(func, parameters)
    return final_output


# TODO determine how to create this functions map
# if developers are just sending their own mock pipelines across
# then we need to reference their string function names to the
# appropriate function to run
FUNCTIONS_MAP = {
    'agg1': '',  # agg1
    'agg2': '',  # agg2
    # ...
}


def replace_function_names(obj):
    """
    Replaces function names found in the input object with new names defined in a dictionary called FUNCTIONS_MAP.

    :param obj (object): The object to be processed. Can be a string, list, dictionary, or any other object.
    :return: A new object with any function names replaced with their corresponding replacement values from FUNCTIONS_MAP.
    """
    if isinstance(obj, str):
        return FUNCTIONS_MAP.get(obj)
    elif isinstance(obj, list):
        return [replace_function_names(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: replace_function_names(value) for key, value in obj.items()}
    else:
        return obj


@learning_observer.auth.teacher
async def generic_websocket(request):
    """
    This function handles a generic WebSocket connection. It receives JSON-formatted data from the client,
    validates it against a JSON schema, and responds with processed data in JSON format.

    In this workflow, the client starts the interaction by sending an initial message.

    :param request: An object representing the incoming WebSocket connection request.
    """
    # Create a WebSocketResponse object and prepare it for receiving messages.
    ws = aiohttp.web.WebSocketResponse(receive_timeout=0.1)
    await ws.prepare(request)

    # Initialize variables to hold course and module data, a runtime object, and student data.
    client_data = None
    course_id = None
    module_id = None
    runtime = learning_observer.runtime.Runtime(request)
    roster = None
    course_aggregator_module = None
    default_data = None
    student_state_fetcher = None

    # Start an infinite loop to continuously receive and process incoming data.
    while True:
        try:
            # Receive data from the client and validate it against a JSON schema.
            client_data = await ws.receive_json()
            jsonschema.validate(client_data, learning_observer.communication_protocol.websocket_receive)

        except jsonschema.ValidationError as e:
            # Handle a validation error by logging a message and continuing the loop.
            debug_log('Something is wrong with the data received from the client:\n', e)
            continue

        except (TypeError, ValueError):
            # Handle a type error or value error by checking if the WebSocket has been closed.
            if (await ws.receive()).type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                return aiohttp.web.Response(text="This never makes it back....")

        except asyncio.exceptions.TimeoutError:
            # Handle a timeout error by checking if client_data is None and continuing the loop.
            if client_data is None:
                continue

        # Check if the WebSocket connection has been closed and return an appropriate response.
        if ws.closed:
            debug_log("Socket closed. This should never appear, however.")
            return aiohttp.web.Response(text="This never makes it back....")

        # Check if the course or module ID has changed.
        new_course = course_id != client_data['course_id']
        new_module = module_id != client_data['module']

        # If the course ID has changed, fetch the course roster.
        if new_course:
            course_id = client_data['course_id']
            roster = await rosters.courseroster(request, course_id)

        # If the module ID has changed, find the corresponding course aggregator module.
        if new_module:
            # If we are in dev mode and receive an object, then use the obj as our aggregator
            module = client_data['module']
            if learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV and isinstance(module, dict):
                # check that the module conforms to our necessary schema

                try:
                    jsonschema.validate(module, learning_observer.communication_protocol.module_schema)
                except jsonschema.ValidationError as e:
                    debug_log('Something is wrong with the module object received from the client:\n', e)
                    continue

                # TODO the pipeline of this code is not fully finished
                # we are still waiting on the FUNCTION_MAP downstream to be finished
                # before this code will runction
                course_aggregator_module = replace_function_names(module)
                module_id = json.dumps(module)
                default_data = course_aggregator_module.get('default_data', {})
            # otherwise just fetch the module from the registered items
            else:
                module_id = module
                course_aggregator_module, default_data = find_course_aggregator(module_id)

            # If the course aggregator module cannot be found, raise an HTTPBadRequest error.
            if course_aggregator_module is None:
                debug_log("Bad module: ", module_id)
                available = learning_observer.module_loader.course_aggregators()
                debug_log("Available modules: ", [available[key]['short_id'] for key in available])
                raise aiohttp.web.HTTPBadRequest(text="Invalid module: {}".format(module_id))

            # Get the list of aggregator functions from the course aggregator module.
            aggregators = course_aggregator_module.get('aggregator', [])

        # If the course or module ID has changed, fetch student data for the new module.
        if new_course or new_module:
            student_state_fetcher = fetch_student_state(
                course_id,
                module_id,
                course_aggregator_module,
                roster,
                default_data
            )

        # Fetch the student data using the student_state_fetcher function
        sd = await student_state_fetcher()
        data = {
            "student_data": sd   # Per-student list
        }

        # Process the aggregator functions with the received client data and add the results to the response data.
        #
        # We run process function for each item in the highest level list of aggregators as users may
        # want to see data from multiple aggregators.
        # ```
        # # simple
        # aggregator = [nlp_indicators, time_on_task]
        # # pipeline
        # # if you first need to fetch student text
        # aggregator = [[student_text, nlp_indicators], time_on_task]
        # ```
        # NOTE right now if you are using the pipeline, there expects a prev_output though this can be modified
        # that's leftover from hacking it together
        #
        # TODO we should populate a dictionary with the function names, we'll need to str(list of functions) though
        data['aggregator'] = [await process_function(agg, client_data['parameters']['aggregators'][i], runtime, sd) for i, agg in enumerate(aggregators)]

        # Send the processed data back to the client.
        await ws.send_json(data)

        # Wait for the specified refresh time before continuing the loop.
        await asyncio.sleep(client_data['parameters'].get('refresh', 0.5))


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
