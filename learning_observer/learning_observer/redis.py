'''
Little helper for per-thread connection pooling. We want just one
redis connection.
'''

import asyncio_redis

redis_connection = None


async def connect():
    '''
    Connect to redis
    '''
    global redis_connection
    print(redis_connection)
    if redis_connection is None:
        redis_connection = await asyncio_redis.Connection.create()
        print(redis_connection)


async def connection():
    '''
    Returns our connection. Connects if needed.

    This is shorthand. It's not clear if this is the right abstraction,
    since it makes for a mess of awaits.
    '''
    connect()
    return redis_connection()
