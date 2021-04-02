'''
This is a stubbed-in version of the XMPP send/receive code. It is
helpful for development and debugging.
'''

import collections
import asyncio

# We should eventually have a list of queues: One for each
# subscriber. For now, we only support one subscriber.
queue = collections.defaultdict(asyncio.Queue)


class SendStub():
    '''
    Minimal class for sending events over a channel. Perhaps
    this should be a closure?
    '''
    def __init__(self, channel='dummy'):
        self.channel = channel

    async def send_event(self, mbody):
        queue[self.channel].put_nowait(mbody)
        return True


class ReceiveStub():
    '''
    Minimal class for receiving events over a channel. Perhaps
    this should be a closure?
    '''
    def __init__(self, channel='dummy'):
        self.channel = channel

    async def receive(self):
        return await queue[self.channel].get()


if __name__ == '__main__':
    async def main():
        s = SendStub()
        r = ReceiveStub()
        await s.send_event("hi")
        await s.send_event("bye")
        r1 = await r.receive()
        print(r1)
        r1 = await r.receive()
        print(r1)

    asyncio.run(main())
