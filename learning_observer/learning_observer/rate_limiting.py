'''
This file defines a rate limit decorator function.
'''
import asyncio
import collections
import functools
import inspect
import time

import learning_observer.auth
import learning_observer.constants

RATE_LIMITERS = {}
RL_LOCK = asyncio.Lock()


def create_rate_limiter(service_name):
    '''Factory function for rate limiters with closure over service name'''
    async def check_rate_limit(user_id):
        '''Reusable rate limiter with service-specific settings'''
        # TODO fetch from pmss/define appropriate window
        max_requests = 2
        window_seconds = 60

        async with RL_LOCK:
            now = time.time()

            # Initialize user/service tracking
            key = f'rate_limit:{service_name}:{user_id}'
            if key not in RATE_LIMITERS:
                RATE_LIMITERS[key] = collections.deque()

            # Expire old requests
            timestamps = RATE_LIMITERS[key]
            while timestamps and (now - timestamps[0]) > window_seconds:
                timestamps.popleft()

            if len(timestamps) >= max_requests:
                return False

            timestamps.append(now)
            return True

    return check_rate_limit


def rate_limited(service_name):
    '''Decorator for async functions needing rate limiting'''
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the appropriate rate limiter
            if 'runtime' not in kwargs:
                raise TypeError(f'`{func.__name__}` requires `runtime` keyword argument for checking rate limits.')

            runtime = kwargs['runtime']

            check_limit = create_rate_limiter(service_name)

            # Check rate limits before execution
            request = runtime.get_request()
            user = await learning_observer.auth.get_active_user(request)
            user_id = user[learning_observer.constants.USER_ID]
            if not await check_limit(user_id):
                raise PermissionError(f'Rate limit exceeded for {service_name} service')
            
            function_signature = inspect.signature(func)
            if 'runtime' not in function_signature.parameters:
                kwargs = {k: v for k, v in kwargs.items() if k != 'runtime'}

            return await func(*args, **kwargs)
        return wrapper
    return decorator
