'''
Pubsub for redis

redis is nice for medium-scale. It doesn't seem quite as scalable as
xmpp (at least on paper), but it's easy to develop for, easy to
maintain, and should be nice for pilot tests.

Note that redis does not guarantee delivery. This ought to notify the
receiver to dequeue events, rather than sending events directly.
'''

import asyncio
import asyncio_redis


class RedisSend():
    '''
    Simple pubsub sender. To use:
    >> sender = RedisSend("channel-1")
    >> sender.connect()
    >> sender.send_event("Hello!")
    '''
    def __init__(self, channel='test_channel', debug_log=lambda x: None):
        '''
        
        '''
        self.s_connection = None
        self.channel = channel
        self.debug_log = debug_log
        self.debug_log("Redis send created")

    async def connect(self):
        self.s_connection = await asyncio_redis.Connection.create()
        self.debug_log("Redis send connected")

    async def send_event(self, mbody):
        if self.s_connection is None:
            await self.connect()
            self.debug_log("Redis send reconnected")
        n = await self.s_connection.publish(self.channel, mbody)
        self.debug_log("Sent event to "+str(n))


class RedisReceive():
    def __init__(self, channel='test_channel', debug_log=lambda x: None):
        self.r_connection = None
        self.subscriber = None
        self.channel = channel
        self.debug_log = debug_log
        self.debug_log("Redis receive initialized")

    async def connect(self):
        self.r_connection = await asyncio_redis.Connection.create()
        self.subscriber = await self.r_connection.start_subscribe()
        await self.subscriber.subscribe([self.channel])
        self.debug_log("redis receive connected")

    async def receive(self):
        if self.r_connection is None:
            self.debug_log("redis receive reconnected")
            await self.connect()
        self.debug_log("awaiting event")
        item = await self.subscriber.next_published()
        self.debug_log("Got event!")
        return item.value


if __name__ == '__main__':
    async def main():
        sender = RedisSend()
        await sender.connect()
        receiver = RedisReceive()
        await receiver.connect()
        await sender.send_event("hi")
        await sender.send_event("bye")
        received_msg = await receiver.receive()
        print(received_msg)
        received_msg = await receiver.receive()
        print(received_msg)

    asyncio.run(main())
