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
    '''Creates a rate limiter for a specific service.
    '''
    async def check_rate_limit(id):
        '''Check if id has hit the rate limit.

        Uses sliding window to track recent requests. Returns
        whether the current request should be allowed based on
        the configured limits.
        '''
        # TODO fetch from pmss/define appropriate window
        max_requests_per_window = 2
        window_seconds = 60

        async with RL_LOCK:
            now = time.time()

            # Initialize id/service tracking
            limiter_key = f'rate_limit:{service_name}:{id}'
            if limiter_key not in RATE_LIMITERS:
                RATE_LIMITERS[limiter_key] = collections.deque()

            # Expire old requests
            prior_requests_timestamps = RATE_LIMITERS[limiter_key]
            while prior_requests_timestamps and (now - prior_requests_timestamps[0]) > window_seconds:
                prior_requests_timestamps.popleft()

            if len(prior_requests_timestamps) >= max_requests_per_window:
                return False

            prior_requests_timestamps.append(now)
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

            check_rate_limit = create_rate_limiter(service_name)

            # Check rate limits before execution
            request = runtime.get_request()
            user = await learning_observer.auth.get_active_user(request)
            user_id = user[learning_observer.constants.USER_ID]
            if not await check_rate_limit(user_id):
                raise PermissionError(f'Rate limit exceeded for {service_name} service')
            
            function_signature = inspect.signature(func)
            if 'runtime' not in function_signature.parameters:
                kwargs = {k: v for k, v in kwargs.items() if k != 'runtime'}

            return await func(*args, **kwargs)
        return wrapper
    return decorator
