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

import asyncio

import aiohttp
import aiohttp.web

import uvloop

import learning_observer.settings as settings
import learning_observer.routes as routes
import learning_observer.prestartup
import learning_observer.webapp_helpers

from learning_observer.log_event import debug_log

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)

# Run argparse
args = settings.parse_and_validate_arguments()


def create_app():
    # Load the settings file
    settings.load_settings(args.config_file)
    # Check that everything is configured correctly,
    # and initialize anything which needs initialization
    learning_observer.prestartup.startup_checks_and_init()
    # Initialize the streaming analytics framework
    learning_observer.stream_analytics.init()
    # Create the application
    app = aiohttp.web.Application()

    # Set up the routing table
    routes.add_routes(app)

    # Set up all the middlewares, sessions, and things
    learning_observer.webapp_helpers.setup_cors(app)
    learning_observer.webapp_helpers.setup_middlewares(app)
    learning_observer.webapp_helpers.setup_session_storage(app)
    return app

app=create_app()

# Feature flag!
#
# uvloop claims to make async Python much faster.
if 'uvloop' in settings.settings.get("feature_flags", {}):
    debug_log("Running with uvloop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    debug_log("Running without uvloop")

port = settings.settings.get("server", {}).get("port", None)
runmode = settings.settings.get("config", {}).get("run_mode", None)

if port is None and runmode == 'dev':
    port = learning_observer.webapp_helpers.find_open_port()

if __name__ == '__main__':
    if "--watchdog" in sys.argv:
        print("Watchdog mode")

aiohttp.web.run_app(app, port=port)
