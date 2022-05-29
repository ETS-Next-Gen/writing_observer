'''
This file contains assorted middlewares.

Perhaps we'll rename it and add things like CORS and what-not as well.
'''
from learning_observer.log_event import debug_log


async def request_logger_middleware(request, handler):
    '''
    Print all hits. Helpful for debugging. Should eventually go into a
    log file.
    '''
    debug_log(request)


async def add_nocache(request, response):
    '''
    This prevents the browser from caching pages.

    Browsers do wonky things when logging in / out, keeping old pages
    around. Caching generally seems like a train wreck for this system.
    There's a lot of cleanup we can do to make this more robust, but
    for now, this is a good enough solution.
    '''
    if '/static/' not in str(request.url):
        response.headers['cache-control'] = 'no-cache'
