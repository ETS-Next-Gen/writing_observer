import json

import aiohttp

import synthetic_student_data

def static_student_data_handler(request):
    return aiohttp.web.json_response(json.load(open("static/student_data.js")))

student_data_handler = static_student_data_handler
student_data_handler = lambda x: aiohttp.web.json_response(synthetic_student_data.synthetic_data())
