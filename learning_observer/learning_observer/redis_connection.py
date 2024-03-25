'''
This was designed as a helper for per-thread connection pooling (we want
just one redis connection). This was necessary with asyncio_redis. We ported
to redis.asyncio, and right now, a lot of this design and code is obsolete.
Right now, it's easy to switch around, but this should be modernized once we're
confident using redis.asyncio. It handles a lot of what we do manually inside
the library.
'''

import redis.asyncio


from learning_observer.log_event import debug_log


REDIS_CONNECTION = None


async def connect():
    '''
    Connect to redis
    '''
    global REDIS_CONNECTION
    if REDIS_CONNECTION is None:
        REDIS_CONNECTION = redis.asyncio.Redis()
    await REDIS_CONNECTION.ping()


async def connection():
    '''
    Returns our connection. Connects if needed.

    This is shorthand. It's not clear if this is the right abstraction,
    since it makes for a mess of awaits.
    '''
    await connect()
    return REDIS_CONNECTION


async def keys():
    '''
    Return all the keys in the database. This might take a while on production
    installs, but is super-helpful in debugging.
    '''
    return [key.decode('utf-8') for key in await (await connection()).keys()]


async def get(key):
    '''
    Get a key. We should eventually do multi-gets. Returns a future.
    '''
    return await (await connection()).get(key)


async def set(key, value, expiry=None):
    '''
    Set a key. We should eventually do multi-sets. Returns a future.
    '''
    return await (await connection()).set(key, value, expiry)


async def delete(key):
    '''
    Delete a key. Returns a future.
    '''
    return await (await connection()).delete(key)
