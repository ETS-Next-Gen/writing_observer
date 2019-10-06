import time

import asyncio
from aiohttp import web
import aiohttp_cors
from aiohttp.web import middleware

import orm

async def debug_signal(request, handler):
    print(request)

routes = web.RouteTableDef()

@routes.get('/')
async def hello(request):
    print("Request made!")
    server_data = {
        'time': time.time(),
        'origin': request.headers.get('Origin', ''),
        'agent': request.headers.get('User-Agent', ''),
        'ip': request.headers.get('X-Real-IP', '')
    }
    client_data = await request.json()
    event = {
        'server': server_data,
        'client': client_data
    }
    # response = await orm.insert_event (username, docstring, event):
    print(event)
    print(server_data)
    return web.Response(text="Acknowledged!")

app = web.Application()

app.on_response_prepare.append(debug_signal)

app.add_routes([
    web.get('/webapi/', hello),
    web.post('/webapi/', hello),
])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

web.run_app(app, port=8888)
