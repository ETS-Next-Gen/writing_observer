#!/usr/bin/env python
# ==================================
# WebSocketTest.py
# Collin F. Lynch.
#
# This is a simple piece of code that I put together to
# ping the websockets API of the server just to confirm
# that it is running.
#
# Just gets a reject at the moment which is fine. 


import asyncio
import websockets

def test_url(url, data=""):
    async def inner():
        async with websockets.connect(url) as websocket:
            await websocket.send(data)
    return asyncio.get_event_loop().run_until_complete(inner())

test_url("wss://writing.csc.ncsu.edu/wsapi/in")
