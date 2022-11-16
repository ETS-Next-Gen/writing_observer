#!/usr/bin/env python
# Simple Asyncio redis test.


import asyncio
import asyncio_redis


async def example():
    # Create Redis connection
    connection = await asyncio_redis.Connection.create(host='localhost', port=6379)

    # Set a key
    await connection.set('my_key', 'my_value')

    # When finished, close the connection.
    connection.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
