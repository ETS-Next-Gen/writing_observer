'''
This is the main file for processing event data for student writing. This
system is designed for our writing analysis project, but is designed to
generalize to learning process data from multiple systems. We have a few
small applications we are testing this system with as well (e.g. dynamic
assessment).
'''

import json
import os

import aiohttp
import aiohttp_cors

import pathvalidate

import init  # Odd import which makes sure we're set up
import event_pipeline
import student_data

routes = aiohttp.web.RouteTableDef()
app = aiohttp.web.Application()


async def request_logger_middleware(request, handler):
    '''
    Print all hits. Helpful for debugging. Should eventually go into a
    log file.
    '''
    print(request)

app.on_response_prepare.append(request_logger_middleware)


def static_file_handler(basepath):
    '''
    Serve static files.

    This can be done directly by nginx on deployment.

    This is very minimal for now: No subdirectories, no gizmos,
    nothing fancy. I avoid fancy when we have user input and
    filenames. Before adding fancy, I'll want test cases of
    aggressive user input.
    '''
    def handler(request):
        # Extract the filename from the request
        filename = request.match_info['filename']
        # Raise an exception if we get anything nasty
        pathvalidate.validate_filename(filename)
        # Check that the file exists
        full_pathname = os.path.join(basepath, filename)
        print(full_pathname)
        if not os.path.exists(full_pathname):
            raise aiohttp.web.HTTPNotFound()
        # And serve pack the file
        return aiohttp.web.FileResponse(full_pathname)
    return handler


# Student data API
app.add_routes([
    aiohttp.web.get('/webapi/student-data/', student_data.student_data_handler),
    aiohttp.web.get('/wsapi/student-data/', student_data.ws_student_data_handler)
])

# Serve static files
app.add_routes([
    aiohttp.web.get('/static/{filename}', static_file_handler("static")),
    aiohttp.web.get('/static/media/{filename}', static_file_handler("media")),
    aiohttp.web.get('/static/media/avatar/{filename}',
                    static_file_handler("media/hubspot_persona_images/")),
])

# Handle web sockets event requests, incoming and outgoing
app.add_routes([
    aiohttp.web.get('/wsapi/in/', event_pipeline.incoming_websocket_handler),
    aiohttp.web.get('/wsapi/out/', event_pipeline.outgoing_websocket_handler)
])

# Handle AJAX event requests, incoming
app.add_routes([
    aiohttp.web.get('/webapi/event/', event_pipeline.ajax_event_request),
    aiohttp.web.post('/webapi/event/', event_pipeline.ajax_event_request),
])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

aiohttp.web.run_app(app, port=8888)
