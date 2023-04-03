from functools import wraps
import json

import learning_observer.kvs


def create_key_from_args(*args, **kwargs):
    key_dict = {'args': args, 'kwargs': kwargs}
    key_str = json.dumps(key_dict, sort_keys=True)
    return key_str


def async_memoization():
    # TODO how should we default here if memoization_cache doesn't exist?
    cache_backend = learning_observer.kvs.KVS_DICT['memoization_cache']()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = create_key_from_args(args, kwargs)
            if key in await cache_backend.keys():
                return await cache_backend[key]
            result = await func(*args, **kwargs)
            await cache_backend.set(key, result)
            return result
        return wrapper
    return decorator
