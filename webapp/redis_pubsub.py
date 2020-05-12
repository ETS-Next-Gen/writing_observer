'''
Pubsub for redis

Note that redis does not guarantee delivery. This ought to notify the
receiver to dequeue events, rather than sending events directly.
'''

import asyncio
import asyncio_redis

class SendStub():
    def __init__(self, channel='test_channel'):
        self.s_connection = None
        self.channel = channel
        print("Redis send created")

    async def connect(self):
        self.s_connection = await asyncio_redis.Connection.create()
        print("Redis send connected")

    async def send_event(self, mbody):
        if self.s_connection is None:
            await self.connect()
            print("Redis send reconnected")
        n = await self.s_connection.publish('dummy_channel', mbody)
        print("Sent event to "+str(n))

class ReceiveStub():
    def __init__(self, channel='test_channel'):
        self.r_connection = None
        self.subscriber = None
        self.channel = channel
        print("Redis receive initialized")

    async def connect(self):
        self.r_connection = await asyncio_redis.Connection.create()
        self.subscriber = await self.r_connection.start_subscribe()
        await self.subscriber.subscribe([self.channel])
        print("redis receive connected")

    async def receive(self):
        if self.r_connection is None:
            print("redis receive reconnected")
            await self.connect()
        print("awaiting event")
        item = await self.subscriber.next_published()
        print("Got event!")
        return item.value

if __name__ == '__main__':
    async def main():
        s = SendStub()
        await s.connect()
        r = ReceiveStub()
        await r.connect()
        await s.send_event("hi")
        await s.send_event("bye")
        r1 = await r.receive()
        print(r1)
        r1 = await r.receive()
        print(r1)

    asyncio.run(main())
