import time

import asyncio
import aiohttp
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

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            print(msg)
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

app = web.Application()

app.on_response_prepare.append(debug_signal)

app.add_routes([web.get('/wsapi/', websocket_handler)])

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
