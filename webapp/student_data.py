import asyncio
import json
import random

import aiohttp

import tsvx

import synthetic_student_data

import stream_analytics.helpers
import stream_analytics.writing_analysis
import kvs

def authenticated(request):
    '''
    Dummy function to tell if a request is logged in
    '''
    return True


async def static_student_data_handler(request):
    '''
    Populate static / mock-up dashboard with static fake data
    '''
    return aiohttp.web.json_response({
        "new_student_data": json.load(open("static/student_data.js"))
    })


async def generated_student_data_handler(request):
    '''
    Populate static / mock-up dashboard with static fake data dynamically
    '''
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


async def real_student_data():
    teacherkvs = kvs.KVS()
    students = []
    student_list_fp = tsvx.reader(open("static_data/class_lists/test_users.tsvx"))
    for student in student_list_fp:
        print(student.user_id)
        # TODO: Evaluate whether this is a bottleneck.
        #
        # mget is faster than ~50 gets. But some online benchmarks show both taking
        # microseconds, to where it might not matter.
        #
        # For most services, though, this would be a huge bottleneck.
        student_data = {
            'id': student.user_id,
            'name': student.name,
            'full_name': student.full_name,
            'email': student.email,
            'phone': student.phone,

            # Defaults if we have no data. If we have data, this will be overwritten.
            'stream_analytics.writing_analysis.reconstruct': {
                'text': '[No data]',
                'position': 0,
                'edit_metadata': {'cursor': [2], 'length': [1]}
            },
            'stream_analytics.writing_analysis.time_on_task': {'saved_ts': -1, 'total-time-on-task': 0},

            # Obsolete stuff below. We're gradually modernizing this.
            'address': "----",
            'avatar': "avatar-{number}".format(number=random.randint(0, 14)),
            'ici': random.uniform(100, 1000),
            'essay_length': 7,
            'essay': "Test text",
            'writing_time': 67,
            'text_complexity': random.uniform(3, 9),
            'google_doc': "https://docs.google.com/document/d/1YbtJGn7ida2IYNgwCFk3SjhsZ0ztpG5bMzA3WNbVNhU/edit",
            'time_idle': 676,
            'outline': [{"section": "Problem "+str(i+1),
                         "length": random.randint(1, 300)} for i in range(5)],
            'revisions': {}
        }
        for sa_module in SA_MODULES:
            key = stream_analytics.helpers.make_key(
                sa_module,
                student.user_id, # TODO: Should this be safe_user_id?
                stream_analytics.helpers.KeyStateType.EXTERNAL)
            data = await teacherkvs[key]
            if data is not None:
                student_data[stream_analytics.helpers.fully_qualified_function_name(sa_module)] = data
        print(student_data)
        students.append(student_data)
    student_list_fp.close()
    return students


async def ws_real_student_data_handler(request):
    print("Serving")
    # External:writing-time-on-task:tsu-ts-test-user-13
    # External:reconstruct-writing:tsu-ts-test-user-17
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    if not authenticated(request):
        await ws.send_json({
            "logged_in": False
        })
        return ws

    # Grab student list, and deliver to the client
    while True:
        await ws.send_json({"new_student_data": synthetic_student_data.paginate(
            await real_student_data(), 4)})
        await asyncio.sleep(0.2)


async def ws_dummy_student_data_handler(request):
    print("Serving")
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
