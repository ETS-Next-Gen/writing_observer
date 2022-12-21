'''
This file contains assorted middlewares and helpers
'''
import errno
import socket

import aiohttp_cors

import aiohttp_session
import aiohttp_session.cookie_storage

import learning_observer.auth
from learning_observer.log_event import debug_log
import learning_observer.settings as settings


async def request_logger_middleware(request, handler):
    '''
    Print all hits. Helpful for debugging. Should eventually go into a
    log file.
    '''
    debug_log(request)


async def add_nocache_middleware(request, response):
    '''
    This prevents the browser from caching pages.

    Browsers do wonky things when logging in / out, keeping old pages
    around. Caching generally seems like a train wreck for this system.
    There's a lot of cleanup we can do to make this more robust, but
    for now, this is a good enough solution.
    '''
    if '/static/' not in str(request.url):
        response.headers['cache-control'] = 'no-cache'


def setup_middlewares(app):
    '''
    This is a helper function to setup middlewares.
    '''
    app.on_response_prepare.append(request_logger_middleware)
    # Avoid caching. We should be more specific about what we want to
    # cache.
    app.on_response_prepare.append(add_nocache_middleware)
    app.middlewares.append(learning_observer.auth.auth_middleware)


def setup_session_storage(app):
    '''
    This is a helper function to setup session storage.
    '''
    aiohttp_session.setup(app, aiohttp_session.cookie_storage.EncryptedCookieStorage(
        learning_observer.auth.fernet_key(settings.settings['aio']['session_secret']),
        max_age=settings.settings['aio']['session_max_age']))


def find_open_port():
    """
    Find an open port to run on.

    By default, run on port 8888. If in use, move up ports, until we find
    one that is not in use.

    Returns:
        int: The open port.
    """
    port = 8888
    bound = False
    while not bound:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            bound = True
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                bound = False
                port = port + 1
            else:
                raise
        s.close()
    return port


def setup_cors(app):
    '''
    This is a helper function to setup CORS.

    This setup is overly broad. We need this for incoming events
    and similar, but we don't want to expose the entire API
    through this as we do here.

    TODO: Handle auth / auth more specifically on individual routes.
    '''
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
