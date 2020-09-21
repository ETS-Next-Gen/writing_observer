'''
This generates dashboard from student data.

TODO: Rename to something better. Perhaps words like:
* Dashboard
* Outgoing
'''

import asyncio
import json
import random
import time

import aiohttp

import tsvx

import util

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


def downsample(data):
    pass


def adhoc_writing_observer_clean(student_data):
    '''
    HACK HACK HACK HACK

    We:
    * Compute text length
    * Cut down the text to just what the client needs to receive (we
      don't want to send 30 full essays)

    This really needs to be made into part of a generic
    aggregator... But we're not there yet.

    TODO: Make aggregator, including these transformations on the
    teacher-facing dashboard end.
    '''
    text = student_data['stream_analytics.writing_analysis.reconstruct']['text']
    if text is None:
        student_data['writing-observer-compiled'] = {
            "text": "[None]",
            "character-count": 0
        }
        return student_data

    character_count = len(text)
    cursor_position = student_data['stream_analytics.writing_analysis.reconstruct']['position']

    # Compute the portion of the text we want to return.
    LENGTH = 103
    BEFORE = int(LENGTH * 2 / 3)
    # We step backwards and forwards from the cursor by the desired number of characters
    start = max(0, int(cursor_position - BEFORE))
    end = min(character_count - 1, start + LENGTH)
    # And, if we don't have much text after the cursor, we adjust the beginning
    print(start, cursor_position, end)
    start = max(0, end - LENGTH)
    # Split on a word boundary, if there's one close by
    print(start, cursor_position, end)
    while end < character_count and end - start < LENGTH + 10 and not text[end].isspace():
        end += 1

    print(start, cursor_position, end)
    while start > 0 and end - start < LENGTH + 10 and not text[start].isspace():
        start -= 1

    print(start, cursor_position, end)
    clipped_text = text[start:cursor_position - 1] + "❙" + text[max(cursor_position - 1, 0):end]
    # Yes, this does mutate the input. No, we should. No, it doesn't matter, since the
    # code needs to move out of here. Shoo, shoo.
    student_data['writing-observer-compiled'] = {
        "text": clipped_text,
        "character-count": character_count
    }
    # Remove things which are too big to send back. Note: Not benchmarked, so perhaps not too big
    del student_data['stream_analytics.writing_analysis.reconstruct']['text']
    # We should downsample, rather than removing
    del student_data['stream_analytics.writing_analysis.reconstruct']['edit_metadata']
    return student_data


def adhoc_writing_observer_aggregate(student_data):
    '''
    Compute and aggregate cross-classroom.

    HACK HACK HACK: To abstract out into writing observer subsystem.
    '''
    max_idle_time = 0
    max_time_on_task = 0
    max_character_count = 0
    for student in student_data:
        max_character_count = max(max_character_count, student['writing-observer-compiled']['character-count'])
        max_time_on_task = max(max_time_on_task, student['stream_analytics.writing_analysis.time_on_task']["total-time-on-task"])
    return {
        'max-character-count': max_character_count,
        'max-time-on-task': max_time_on_task,
        # TODO: Should we aggregate this in some way? If we run on multiple servers, this is susceptible to drift.
        # That could be jarring; even a few seconds error could be an issue in some contexts.
        'current-time': time.time()
    }


def real_student_data(course_id, roster):
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
                    'text': None,
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
            # For most services (e.g. a SQL database), this would be a huge bottleneck. redis might
            # be fast enough that it doesn't matter? Dunno.
            for sa_module in SA_MODULES:
                key = stream_analytics.helpers.make_key(
                    sa_module,
                    student_id,
                    stream_analytics.helpers.KeyStateType.EXTERNAL)
                data = await teacherkvs[key]
                if data is not None:
                    student_data[stream_analytics.helpers.fully_qualified_function_name(sa_module)] = data
            print(student_data)
            students.append(adhoc_writing_observer_clean(student_data))

        return students
    return rsd


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

    print("Grabbing roster for " + str(course_id))
    roster = await rosters.courseroster(request, course_id)
    # Grab student list, and deliver to the client
    rsd = real_student_data(course_id, roster)
    while True:
        sd = await rsd()
        await ws.send_json({
            "aggegated-data": adhoc_writing_observer_aggregate(sd),  # Common to all students
            "new-student-data": util.paginate(sd, 4)                 # Per-student list
        })
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
