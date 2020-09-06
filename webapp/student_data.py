'''
This generates dashboard from student data.

TODO: Rename to something better. Perhaps words like:
* Dashboard
* Outgoing
'''

import asyncio
import json
import random

import aiohttp

import tsvx

import synthetic_student_data

import stream_analytics.helpers
import stream_analytics.writing_analysis
import kvs

import authutils
import rosters

def authenticated(request):
    '''
    Dummy function to tell if a request is logged in
    '''
    return True


async def static_student_data_handler(request):
    '''
    Populate static / mock-up dashboard with static fake data
    '''
    course_id = int(request.match_info['course_id'])

    return aiohttp.web.json_response({
        "new_student_data": json.load(open("static/student_data.js"))
    })


async def generated_student_data_handler(request):
    '''
    Populate static / mock-up dashboard with static fake data dynamically
    '''
    course_id = int(request.match_info['course_id'])

    return aiohttp.web.json_response({
        "new_student_data": synthetic_student_data.synthetic_data()
    })


# TODO: The decorator should collect this list.
#
# We'll need to be a bit smarter about routing dashboards to analytics
# to do this. Right now, this is specific to writing analysis.
SA_MODULES = [
    stream_analytics.writing_analysis.reconstruct,
    stream_analytics.writing_analysis.time_on_task
]


async def real_student_data(course_id, roster):
    teacherkvs = kvs.KVS()
    students = []
    for student in roster:
        print(student)
        student_data = {
            # We're copying Google's roster format here.
            #
            # It's imperfect, and we may want to change it later, but it seems
            # better than reinventing our own standard.
            'profile': {
                'name': {
                    'fullName': student['profile']['name']['fullName']
                },
                'photoUrl': student['profile']['photoUrl'],
                'emailAddress': student['profile']['emailAddress'],
            },
            "courseId": course_id,
            "userId": student['userId'],  # TODO: Encode? 

            # Defaults if we have no data. If we have data, this will be overwritten.
             'stream_analytics.writing_analysis.reconstruct': {
                'text': '[No data]',
                'position': 0,
                'edit_metadata': {'cursor': [2], 'length': [1]}
            },
            'stream_analytics.writing_analysis.time_on_task': {'saved_ts': -1, 'total-time-on-task': 0},
        }
        # TODO/HACK: Only do this for Google data. Make this do the right thing for synthetic data.
        google_id = student['userId']
        student_id = authutils.google_id_to_user_id(google_id)
        # TODO: Evaluate whether this is a bottleneck.
        #
        # mget is faster than ~50 gets. But some online benchmarks show both taking
        # microseconds, to where it might not matter.
        #
        # For most services, though, this would be a huge bottleneck.
        for sa_module in SA_MODULES:
            key = stream_analytics.helpers.make_key(
                sa_module,
                student_id,
                stream_analytics.helpers.KeyStateType.EXTERNAL)
            data = await teacherkvs[key]
            if data is not None:
                student_data[stream_analytics.helpers.fully_qualified_function_name(sa_module)] = data
        print(student_data)
        students.append(student_data)
    return students


async def ws_real_student_data_handler(request):
    print("Serving")
    course_id = int(request.match_info['course_id'])
    # External:writing-time-on-task:tsu-ts-test-user-13
    # External:reconstruct-writing:tsu-ts-test-user-17
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    if not authenticated(request):
        await ws.send_json({
            "logged_in": False
        })
        return ws

    roster = await rosters.courseroster(request, course_id)
    # Grab student list, and deliver to the client
    while True:
        print("Grabbing roster for "+str(course_id))

        #await ws.send_json({"new_student_data": synthetic_student_data.paginate(
        #    roster, 4)})

        await ws.send_json({"new_student_data": synthetic_student_data.paginate(
            await real_student_data(course_id, roster), 4)})
        await asyncio.sleep(0.5)


async def ws_dummy_student_data_handler(request):
    print("Serving")
    course_id = int(request.match_info['course_id'])
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    if authenticated(request):
        await ws.send_json({
            "new_student_data": synthetic_student_data.synthetic_data()
        })
    else:
        await ws.send_json({
            "logged_in": False
        })


ws_student_data_handler = ws_real_student_data_handler

student_data_handler = generated_student_data_handler
