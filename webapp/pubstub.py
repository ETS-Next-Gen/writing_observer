'''
This is a stubbed-in version of the XMPP send/receive code. It is
helpful for development and debugging.
'''

import asyncio

queue = asyncio.Queue()

class SendStub():
    def send_event(self, mbody, mto=None):
        queue.put_nowait(mbody)

class ReceiveStub():
    async def receive(self):
        return await queue.get()

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
