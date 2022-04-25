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
import learning_observer.middleware


# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)

# Run argparse
args = settings.parse_and_validate_arguments()
# Load the settings file
settings.load_settings(args.config_file)
# Check that everything is configured correctly,
# and initialize anything which needs initialization
learning_observer.prestartup.startup_checks_and_init()
# Create the application
app = aiohttp.web.Application()

# Print all requests. We should remove this in deploy/production.
app.on_response_prepare.append(learning_observer.middleware.request_logger_middleware)
# Avoid caching. We should remove this in deploy/production except
# where needed. In dev, we change static files all the time, so it is
# helpful.
app.on_response_prepare.append(learning_observer.middleware.add_nocache)

# Set up the routing table
routes.add_routes(app)

# Set up CORS. TODO: This is way too much CORS. We'll want to clean this
# up later.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})


aiohttp_session.setup(app, aiohttp_session.cookie_storage.EncryptedCookieStorage(
    learning_observer.auth.fernet_key(settings.settings['aio']['session_secret']),
    max_age=settings.settings['aio']['session_max_age']))

app.middlewares.append(learning_observer.auth.auth_middleware)


print("Running!")
aiohttp.web.run_app(app, port=int(settings.settings.get("server", {}).get("port", 8888)))
