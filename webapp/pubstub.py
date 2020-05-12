'''
This is a stubbed-in version of the XMPP send/receive code. It is
helpful for development and debugging.
'''

import collections
import asyncio

queue = collections.defaultdict(lambda:asyncio.Queue())

class SendStub():
    def __init__(self, channel='dummy'):
        self.channel = channel

    async def send_event(self, mbody):
        queue[self.channel].put_nowait(mbody)
        return True

class ReceiveStub():
    def __init__(self, channel='dummy'):
        self.channel = channel

    async def receive(self):
        return await queue[self.channel].get()

if __name__ == '__main__':
    async def main():
        s = SendStub()
        r = ReceiveStub()
        s.send_event("hi")
        s.send_event("bye")
        r1 = await r.receive()
        print(r1)
        r1 = await r.receive()
        print(r1)

    asyncio.run(main())
