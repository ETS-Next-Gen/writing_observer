'''
This generates dashboard from student data.

TODO: Rename to something better. Perhaps words like:
* Dashboard
* Outgoing
'''

import asyncio
import json
import time

import aiohttp

import learning_observer.util as util

import learning_observer.synthetic_student_data as synthetic_student_data

import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.stream_analytics.writing_analysis as sa_writing_analysis
import learning_observer.kvs as kvs

import learning_observer.paths as paths

import learning_observer.auth
import learning_observer.rosters as rosters


def aggregate_student_data(course_id, module_id, agg_module, roster, default_data={}):
    '''
    Closure remembers course roster, and redis KVS.

    Reopening connections to redis every few seconds otherwise would
    run us out of file pointers.
    '''
    teacherkvs = kvs.KVS()

    async def rsd():
        '''
        Poll redis for student state. This should be abstracted out into a generic
        aggregator API, much like we have a reducer on the incoming end.
        '''
        students = []
        for student in roster:
            # print(student)
            student_data = {
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
            student_data.update(default_data)

            # TODO/HACK: Only do this for Google data. Make this do the right thing
            # for synthetic data.
            google_id = student['userId']
            student_id = learning_observer.auth.google_id_to_user_id(google_id)
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
                    student_id,
                    sa_helpers.KeyStateType.EXTERNAL)
                print(key)
                data = await teacherkvs[key]
                print(data)
                if data is not None:
                    student_data[sa_helpers.fully_qualified_function_name(sa_module)] = data
            cleaner = agg_module.get("cleaner", lambda x:x)
            students.append(cleaner(student_data))

        return students
    return rsd


@learning_observer.auth.teacher
async def ws_course_aggregate_view(request):
    '''
    Handler to aggregate student data, and serve it back to the client
    every half-second to second or so.
    '''
    # print("Serving")
    module_id = request.match_info['module_id']
    course_id = int(request.match_info['course_id'])
    # Find the right module
    agg_module = None

    lomlca = learning_observer.module_loader.class_aggregators()
    for m in lomlca:
        if lomlca[m]['short_id'] == module_id:
            if agg_module is not None:
                raise aiohttp.web.HTTPNotImplemented(text="Duplicate module: "+m)
            agg_module = lomlca[m]
    if agg_module is None:
        raise aiohttp.web.HTTPBadRequest(text="Invalid module: "+m)

    # We need to receive to detect web socket closures.
    ws = aiohttp.web.WebSocketResponse(receive_timeout=0.1)
    await ws.prepare(request)

    roster = await rosters.courseroster(request, course_id)
    # Grab student list, and deliver to the client
    rsd = aggregate_student_data(
        course_id,
        module_id,
        agg_module,
        roster,
        learning_observer.writing_observer.aggregator.DEFAULT_DATA  # TODO
    )
    aggregator = agg_module.get('aggregator', lambda x: None)
    while True:
        sd = await rsd()
        await ws.send_json({
            "aggegated-data": aggregator(sd),                        # Common to all students
            "new-student-data": util.paginate(sd, 4)                 # Per-student list
        })
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


# @learning_observer.auth.teacher
# async def ws_dummy_student_data_handler(request):
#     # print("Serving")
#     module_id = request.match_info['module_id']
#     course_id = int(request.match_info['course_id'])
#     ws = aiohttp.web.WebSocketResponse()
#     await ws.prepare(request)
#     await ws.send_json({
#         "new_student_data": synthetic_student_data.synthetic_data()
#     })


# ws_aggregate_student_data = ws_aggregate_student_data_handler

# student_data_handler = generated_student_data_handler

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


