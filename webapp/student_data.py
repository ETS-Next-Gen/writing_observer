import json

import aiohttp

import synthetic_student_data

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


async def ws_student_data_handler(request):
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

student_data_handler = generated_student_data_handler
