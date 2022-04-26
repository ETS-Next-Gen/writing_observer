'''
Little helper for per-thread connection pooling. We want just one
redis connection.
'''

import asyncio_redis

from learning_observer.log_event import debug_log


REDIS_CONNECTION = None


async def connect():
    '''
    Connect to redis
    '''
    global REDIS_CONNECTION
    if REDIS_CONNECTION is None:
        REDIS_CONNECTION = await asyncio_redis.Connection.create()
        debug_log(REDIS_CONNECTION)


async def connection():
    '''
    Returns our connection. Connects if needed.

    This is shorthand. It's not clear if this is the right abstraction,
    since it makes for a mess of awaits.
    '''
    await connect()
    return REDIS_CONNECTION
