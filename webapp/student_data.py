import json

import aiohttp

import synthetic_student_data


def static_student_data_handler(request):
    '''
    Populate static / mock-up dashboard with static fake data
    '''
    return aiohttp.web.json_response(json.load(open("static/student_data.js")))


def generated_student_data_handler(request):
    '''
    Populate static / mock-up dashboard with static fake data dynamically
    '''
    return aiohttp.web.json_response(synthetic_student_data.synthetic_data())

student_data_handler = generated_student_data_handler
