'''
This generates dashboards from student data.
'''

import asyncio
import json
import numbers
import queue
import time

import aiohttp

import learning_observer.util as util

import learning_observer.synthetic_student_data as synthetic_student_data

import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.kvs as kvs

import learning_observer.paths as paths

import learning_observer.auth
import learning_observer.rosters as rosters

from learning_observer.log_event import debug_log


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
                        'fullName': student['profile']['name']['fullName']
                    },
                    'photoUrl': student['profile']['photoUrl'],
                    'emailAddress': student['profile']['emailAddress'],
                },
                "courseId": course_id,
                "userId": student['userId'],  # TODO: Encode?
            }
            student_state.update(default_data)

            # TODO/HACK: Only do this for Google data. Make this do the right thing
            # for synthetic data.
            google_id = student['userId']
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
                debug_log(key)
                data = await teacherkvs[key]
                debug_log(data)
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
        debug_log("Available modules: ", learning_observer.module_loader.course_aggregators())
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
        roster = [r for r in roster if r['userId'] == student_id]

    # Grab student list, and deliver to the client
    student_state_fetcher = fetch_student_state(
        course_id,
        module_id,
        course_aggregator_module,
        roster,
        default_data
    )
    aggregator = course_aggregator_module.get('aggregator', lambda x: {})
    while True:
        sd = await student_state_fetcher()
        data = {
            "student-data": sd   # Per-student list
        }
        data.update(aggregator(sd))
        await ws.send_json(data)
        # This is kind of an awkward block, but aiohttp doesn't detect
        # when sockets close unless they receive data. We try to receive,
        # and wait for an exception or a CLOSE message.
        try:
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


# Obsolete code, but may be repurposed for student dashboards.
#
# aiohttp.web.get('/wsapi/out/', incoming_student_event.outgoing_websocket_handler)

# async def outgoing_websocket_handler(request):
#     '''
#     This pipes analytics back to the browser. It:
#     1. Handles incoming PubSub connections
#     2. Sends it back to the browser

#     TODO: Cleanly handle disconnects
#     '''
#     debug_log('Outgoing analytics web socket connection')
#     ws = aiohttp.web.WebSocketResponse()
#     await ws.prepare(request)
#     pubsub_client = await pubsub.pubsub_receive()
#     debug_log("Awaiting PubSub messages")
#     while True:
#         message = await pubsub_client.receive()
#         debug_log("PubSub event received")
#         log_event.log_event(
#             message, "incoming_pubsub", preencoded=True, timestamp=True
#         )
#         log_event.log_event(
#             message,
#             "outgoing_analytics", preencoded=True, timestamp=True)
#         await ws.send_str(message)
#     await ws.send_str("Done")


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
