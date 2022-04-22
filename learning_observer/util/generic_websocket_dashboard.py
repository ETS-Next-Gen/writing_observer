'''
This is a test script for a web socket interaction.
'''

import aiohttp
import asyncio

messages = [
    {
        "action": "subscribe",
        "keys": [{
            "source": "da_timeline.visualize.handle_event",
            "KeyField.STUDENT": "guest-225d890e93a6b04c0aefe515b9d2dac9"
        }],
        "refresh": [0.5, "seconds"]
    },
    {
        "action": "subscribe",
        "keys": [{
            "source": "da_timeline.visualize.handle_event",
            "KeyField.STUDENT": "INVALID-STUDENT"
        }],
        "refresh": [2, "seconds"]
    },
    {
        "action": "start"
    }
]


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://localhost:8888/wsapi/generic_dashboard', timeout=0.5) as ws:
            for message in messages:
                await ws.send_json(message)

            async for msg in ws:
                print(msg.type)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("Message")
                    print(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("Error")
                    print(msg)
                    break
    return True

asyncio.run(main())
