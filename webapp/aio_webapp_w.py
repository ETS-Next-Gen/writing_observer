'''
This is the main file for processing event data for student writing. This
system is designed for our writing analysis project, but is designed to
generalize to learning process data from multiple systems. We have a few
small applications we are testing this system with as well (e.g. dynamic
assessment).
'''

import aiohttp
import aiohttp_cors

import init
import event_pipeline


routes = aiohttp.web.RouteTableDef()
app = aiohttp.web.Application()


async def request_logger_middleware(request, handler):
    print(request)

app.on_response_prepare.append(request_logger_middleware)

app.add_routes([
    aiohttp.web.get('/wsapi/in/', event_pipeline.incoming_websocket_handler),
    aiohttp.web.get('/wsapi/out/', event_pipeline.outgoing_websocket_handler)
])

app.add_routes([
    aiohttp.web.get('/webapi/', event_pipeline.ajax_event_request),
    aiohttp.web.post('/webapi/', event_pipeline.ajax_event_request),
])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

aiohttp.web.run_app(app, port=8888)
