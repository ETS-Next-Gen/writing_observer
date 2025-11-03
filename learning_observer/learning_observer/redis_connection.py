'''
This was designed as a helper for per-thread connection pooling (we want
just one redis connection). This was necessary with asyncio_redis. We ported
to redis.asyncio, and right now, a lot of this design and code is obsolete.
Right now, it's easy to switch around, but this should be modernized once we're
confident using redis.asyncio. It handles a lot of what we do manually inside
the library.
'''

import asyncio
import functools

import pmss
import redis.asyncio
import redis.exceptions

import learning_observer.settings
from learning_observer.log_event import debug_log


pmss.register_field(
    name='redis_host',
    type=pmss.pmsstypes.TYPES.hostname,
    description='Determine the host for the redis_connection. Defaults to localhost.',
    default='localhost'
)
pmss.register_field(
    name='redis_port',
    type=pmss.pmsstypes.TYPES.port,
    description='Determine the port for the redis_connection. Defaults to 6379.',
    default=6379
)
pmss.register_field(
    name='redis_password',
    type=pmss.pmsstypes.TYPES.string,
    description='Password token for connectioning to redis_connection',
    default=None
)


REDIS_CONNECTION = None
_RECONNECT_LOCK = asyncio.Lock()


def _new_client():
    """
    Create a new redis.asyncio client with current settings.
    NOTE: We do not ping here to avoid extra round trips under heavy load.
    """
    return redis.asyncio.Redis(
        host=learning_observer.settings.pmss_settings.redis_host(types=['redis_connection']),
        port=learning_observer.settings.pmss_settings.redis_port(types=['redis_connection']),
        # TODO figure out how to properly use None from pmss
        # password=learning_observer.settings.pmss_settings.redis_password(types=['redis_connection'])
    )


async def _close_client(client):
    """
    Best-effort, version-tolerant close that avoids raising on shutdown.
    """
    if client is None:
        return
    try:
        # redis-py 5.x provides aclose(); earlier versions may have async close() or sync close()
        if hasattr(client, "aclose"):
            await client.aclose()
        elif hasattr(client, "close"):
            maybe = client.close()
            if asyncio.iscoroutine(maybe):
                await maybe
        # Also ensure underlying pool is dropped
        if hasattr(client, "connection_pool") and client.connection_pool is not None:
            try:
                await client.connection_pool.disconnect(inuse_connections=True)
            except TypeError:
                # older versions are sync
                client.connection_pool.disconnect()
    except Exception:
        # Don't let shutdown errors cascade
        pass


async def _recreate_connection():
    """
    Recreate the global client safely (once) and atomically.
    """
    global REDIS_CONNECTION
    async with _RECONNECT_LOCK:
        old = REDIS_CONNECTION
        # Another task may have already recreated it while we were waiting
        REDIS_CONNECTION = _new_client()
        # Close the old client outside the critical path (best effort)
        await _close_client(old)


async def connect():
    '''
    Initialize the global Redis client if needed (no ping).
    '''
    global REDIS_CONNECTION
    if REDIS_CONNECTION is None:
        REDIS_CONNECTION = _new_client()


async def connection():
    '''
    Returns our connection. Connects if needed.

    This is shorthand. It's not clear if this is the right abstraction,
    since it makes for a mess of awaits.
    '''
    await connect()
    return REDIS_CONNECTION


_RETRY_EXC = (
    redis.exceptions.ConnectionError, redis.exceptions.TimeoutError,
    ConnectionError, TimeoutError,
    RuntimeError
)


def _with_reconnect(fn):
    """
    Decorator for async Redis ops:
    - Try once.
    - On connection/timeout/runtime failures: recreate client and retry once.
    - No extra PINGs; only recreates on failure.
    """
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except _RETRY_EXC as e:
            # Log at debug level to avoid noise under high throughput
            try:
                debug_log(f"Redis op '{fn.__name__}' failed ({type(e).__name__}); recreating client and retrying once.")
            except Exception:
                pass
            await _recreate_connection()
            return await fn(*args, **kwargs)
    return wrapper


@_with_reconnect
async def keys():
    '''
    Return all the keys in the database. This might take a while on production
    installs, but is super-helpful in debugging.
    '''
    return [key.decode('utf-8') for key in await (await connection()).keys()]


@_with_reconnect
async def get(key):
    '''
    Get a key. Returns a future.
    '''
    return await (await connection()).get(key)


@_with_reconnect
async def mget(keys):
    '''
    Get mutliple keys. Returns a future.
    '''
    return await (await connection()).mget(keys)


@_with_reconnect
async def set(key, value, expiry=None):
    '''
    Set a key. We should eventually do multi-sets. Returns a future.
    '''
    return await (await connection()).set(key, value, expiry)


@_with_reconnect
async def delete(key):
    '''
    Delete a key. Returns a future.
    '''
    return await (await connection()).delete(key)
