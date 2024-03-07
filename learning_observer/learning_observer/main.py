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
import learning_observer.watchdog_observer
import learning_observer.ipython_integration

from learning_observer.log_event import debug_log

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportError("Please use fully-qualified imports")
    sys.exit(-1)

# Run argparse
args = settings.parse_and_validate_arguments()


def configure_event_loop():
    '''
    This is a feature flag. We have not tested / benchmarked it, but
    it claims to make async Python much faster.
    '''
    if 'uvloop' in settings.settings.get("feature_flags", {}):
        debug_log("Running with uvloop")
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    else:
        debug_log("Running without uvloop")


port = None
runmode = None


def create_app():
    '''
    Create the application.

    We've moved this into a function so we can call it from the watchdog
    observer and other places.
    '''
    global port, runmode
    # Load the settings file
    settings.load_settings(args.config_file)
    configure_event_loop()

    # We don't want these to change on a restart.
    # We should check if reloading this module overwrites them.
    if port is None:
        port = settings.settings.get("server", {}).get("port", None)
    if runmode is None:
        runmode = settings.settings.get("config", {}).get("run_mode", None)

    if port is None and runmode == 'dev':
        port = learning_observer.webapp_helpers.find_open_port()

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
    learning_observer.webapp_helpers.setup_session_storage(app)
    learning_observer.webapp_helpers.setup_middlewares(app)
    return app


def shutdown(app):
    '''
    Shutdown the app.
    '''
    app.shutdown()
    app.cleanup()
    return app


def start(app):
    '''
    Start the application.
    '''
    # Reload all imports
    aiohttp.web.run_app(app, port=port)
    return app


print("Arguments:", args)

if args.watchdog is not None:
    print("Watchdog mode")
    # Parse argument to determine watchdog handler
    restart = {
        'restart': learning_observer.watchdog_observer.restart,
        'reimport': learning_observer.watchdog_observer.reimport_child_modules,
    }
    if args.watchdog not in restart:
        print(
            f"Invalid watchdog mode. Valid modes are: {', '.join(restart.keys())}"
        )
        sys.exit(-1)
    fs_event_handler = learning_observer.watchdog_observer.RestartHandler(
        shutdown=shutdown,
        restart=restart[args.watchdog],
        start=start
    )
    learning_observer.watchdog_observer.watchdog(fs_event_handler)

app = create_app()

# This creates the file that tells jupyter how to run our custom
# kernel. This command needs to be ran once (outside of Jupyter)
# before users can get access to the LO Kernel.
if True:
    learning_observer.ipython_integration.load_kernel_spec()

if args.lokernel:
    learning_observer.ipython_integration.start(kernel_only=True, connection_file=args.f, lo_app=app)
elif args.loconsole:
    learning_observer.ipython_integration.start()
else:
    start(app)

# Port printing:
#
# This is kind of ugly. If we want to log the startup port, we can either
# do our own app runner as per:
#   https://stackoverflow.com/questions/44610441/how-to-determine-which-port-aiohttp-selects-when-given-port-0
#
# Or we can introspect:
#   import gc
#   sites = gc.get_referrers(aiohttp.web.TCPSite)
# And find the right object and introspect its port.
#
# To make a dummy test TCPSite:
#    runner = aiohttp.web.AppRunner(aiohttp.web.Application())
#    await runner.setup()
#    foo = aiohttp.web.TCPSite(runner)
#
# Or we can manually find the first open port ourselves.
