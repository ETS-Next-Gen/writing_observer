import json

import aiohttp

def static_student_data_handler(request):
    return aiohttp.web.json_response(json.load(open("static/student_data.js")))


student_data_handler = static_student_data_handler
