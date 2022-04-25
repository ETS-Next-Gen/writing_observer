'''
main.py
=========

This is the main file for processing event data for student writing. This
system is designed for our writing analysis project, but is designed to
generalize to learning process data from multiple systems. We have a few
small applications we are testing this system with as well (e.g. dynamic
assessment).
'''

import sys
import uuid

import aiohttp
import aiohttp_cors
import aiohttp_session
import aiohttp_session.cookie_storage
import aiohttp.web

import learning_observer.auth
import learning_observer.auth.http_basic
import learning_observer.client_config
import learning_observer.dashboard
import learning_observer.rosters as rosters
import learning_observer.module_loader

import learning_observer.settings as settings
import learning_observer.routes as routes
import learning_observer.prestartup


# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)

args = settings.parse_and_validate_arguments()
settings.load_settings(args.config_file)
learning_observer.prestartup.startup_checks_and_init()

# Right now, a lot of code is in top-level files
# Our goal is to be explicit:
# 0) learning_observer.[something].parse_and_validate_arguments()
# 1) learning_observer.settings.load_settings([something from arguments])
# 2) learning_observer.prestartup.startup_checks() (move from init.py)
# 3) learning_observer.server.init()
# 4) learning_observer.routes.add_routes()
# 5) learning_observer.server.run()


async def request_logger_middleware(request, handler):
    '''
    Print all hits. Helpful for debugging. Should eventually go into a
    log file.
    '''
    print(request)


app = aiohttp.web.Application()
app.on_response_prepare.append(request_logger_middleware)
routes.add_routes(app)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})


if 'aio' not in settings.settings or \
   'session_secret' not in settings.settings['aio'] or \
   isinstance(settings.settings['aio']['session_secret'], dict) or \
   'session_max_age' not in settings.settings['aio']:
    print("Settings file needs an `aio` section with a `session_secret`")
    print("subsection containing a secret string. This is used for")
    print("security, and should be set once for each deploy of the platform")
    print("(e.g. if you're running 10 servers, they should all have the")
    print("same secret")
    print()
    print("Please set an AIO session secret in creds.yaml")
    print("")
    print("Please pick a good session secret. You only need to set it once, and")
    print("the security of the platform relies on a strong, unique password there")
    print("")
    print("This sessions also needs a session_max_age, which sets the number of seconds")
    print("of idle time after which a user needs to log back in. 4320 should set")
    print("this to 12 hours.")
    print("")
    print("This should be a long string of random characters. If you can't think")
    print("of one, here's one:")
    print()
    print("aio:")
    print("    session_secret: " + str(uuid.uuid5(uuid.uuid1(), str(uuid.uuid4()))))
    print("    session_max_age: 4320")
    sys.exit(-1)

aiohttp_session.setup(app, aiohttp_session.cookie_storage.EncryptedCookieStorage(
    learning_observer.auth.fernet_key(settings.settings['aio']['session_secret']),
    max_age=settings.settings['aio']['session_max_age']))

app.middlewares.append(learning_observer.auth.auth_middleware)


async def add_nocache(request, response):
    '''
    This prevents the browser from caching pages.

    Browsers do wonky things when logging in / out, keeping old pages
    around. Caching generally seems like a train wreck for this system.
    '''
    if '/static/' not in str(request.url):
        response.headers['cache-control'] = 'no-cache'


app.on_response_prepare.append(add_nocache)

print("Running!")
aiohttp.web.run_app(app, port=int(settings.settings.get("server", {}).get("port", 8888)))
