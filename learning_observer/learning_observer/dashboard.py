'''
This generates dashboards from student data.
'''

import asyncio
import json
import time

import aiohttp

import learning_observer.util as util

import learning_observer.synthetic_student_data as synthetic_student_data

import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.kvs as kvs

import learning_observer.paths as paths

import learning_observer.auth
import learning_observer.rosters as rosters


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
                print(key)
                data = await teacherkvs[key]
                print(data)
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
        print("Bad module: ", module_id)
        print("Available modules: ", learning_observer.module_loader.course_aggregators())
        raise aiohttp.web.HTTPBadRequest(text="Invalid module: " + str(module_id))

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
                print("Socket closed!")
                # By this point, the client is long gone, but we want to
                # return something to avoid confusing middlewares.
                return aiohttp.web.Response(text="This never makes it back....")
        except asyncio.exceptions.TimeoutError:
            # This is the normal code path
            pass
        await asyncio.sleep(0.5)
        # This never gets called, since we return above
        if ws.closed:
            print("Socket closed")
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
