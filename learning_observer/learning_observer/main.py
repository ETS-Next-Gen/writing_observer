'''
This is the main file for processing event data for student writing. This
system is designed for our writing analysis project, but is designed to
generalize to learning process data from multiple systems. We have a few
small applications we are testing this system with as well (e.g. dynamic
assessment).
'''

import hashlib
import os
import sys
import uuid

import aiohttp
import aiohttp_cors
import aiohttp_session
import aiohttp_session.cookie_storage

import pathvalidate

import gitserve.aio_gitserve

# Odd import which makes sure we're set up
import learning_observer.init as init

import learning_observer.admin as admin
import learning_observer.client_config
import learning_observer.incoming_student_event as incoming_student_event
import learning_observer.dashboard as dashboard
import learning_observer.auth_handlers as auth_handlers
import learning_observer.rosters as rosters
import learning_observer.module_loader

import learning_observer.paths as paths
import learning_observer.settings as settings

# If we e.g. `import settings` and `import learning_observer.settings`, we
# will load startup code twice, and end up with double the global variables.
# This is a test to avoid that bug.
if not __name__.startswith("learning_observer."):
    raise ImportErrror("Please use fully-qualified imports")
    sys.exit(-1)


routes = aiohttp.web.RouteTableDef()
app = aiohttp.web.Application()


async def request_logger_middleware(request, handler):
    '''
    Print all hits. Helpful for debugging. Should eventually go into a
    log file.
    '''
    print(request)

app.on_response_prepare.append(request_logger_middleware)


def static_file_handler(filename):
    '''
    Serve a single static file
    '''
    async def handler(request):
        return aiohttp.web.FileResponse(filename)
    return handler


async def index(request):
    '''
    Main page:

    * People who aren't logged in get the login page.
    * People who are get a list of their Google Classroom courses
    '''
    if request['user'] is None:
        return aiohttp.web.FileResponse(paths.static("index.html"))
    return aiohttp.web.FileResponse(paths.static("courselist.html"))


def static_directory_handler(basepath):
    '''
    Serve static files from a directory.

    This could be done directly by nginx on deployment.

    This is very minimal for now: No subdirectories, no gizmos,
    nothing fancy. I avoid fancy when we have user input and
    filenames. Before adding fancy, I'll want test cases of
    aggressive user input.
    '''

    def handler(request):
        '''
        We're in a closure, since we want to configure the directory
        when we set up the path.
        '''
        # Extract the filename from the request
        filename = request.match_info['filename']
        # Raise an exception if we get anything nasty
        pathvalidate.validate_filename(filename)
        # Check that the file exists
        full_pathname = os.path.join(basepath, filename)
        if not os.path.exists(full_pathname):
            raise aiohttp.web.HTTPNotFound()
        # And serve pack the file
        return aiohttp.web.FileResponse(full_pathname)
    return handler


# Allow debugging of memory leaks.  Helpful, but this is a massive
# resource hog. Don't accidentally turn this on in prod :)
if 'tracemalloc' in settings.settings['config'].get("debug", []):
    import tracemalloc
    tracemalloc.start(25)

    def tracemalloc_handler(request):
        '''
        Handler to show tracemalloc stats.
        '''
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        top_hundred = "\n".join((str(t) for t in top_stats[:100]))
        top_stats = snapshot.statistics('traceback')
        top_one = "\n".join((str(t) for t in top_stats[0].traceback.format()))
        return aiohttp.web.Response(text=top_one + "\n\n\n" + top_hundred)
    app.add_routes([
        aiohttp.web.get('/debug/tracemalloc/', tracemalloc_handler),
    ])

# Dashboard API
# This serves up data (currently usually dummy data) for the dashboard
app.add_routes([
    aiohttp.web.get('/webapi/dashboard/{module_id}/{course_id}/', dashboard.student_data_handler),
    aiohttp.web.get('/wsapi/dashboard/{module_id}/{course_id}/', dashboard.ws_student_data_handler)
])

# Serve static files
app.add_routes([
    aiohttp.web.get('/static/{filename}', static_directory_handler(paths.static())),
    aiohttp.web.get('/static/modules/{filename}', static_directory_handler(paths.static("modules"))),
    aiohttp.web.get('/static/3rd_party/{filename}', static_directory_handler(paths.static("3rd_party"))),
    aiohttp.web.get('/static/media/{filename}', static_directory_handler(paths.static("media"))),
    aiohttp.web.get('/static/media/avatar/{filename}',
                    static_directory_handler(paths.static("media/hubspot_persona_images/"))),
])

# Handle web sockets event requests, incoming and outgoing
app.add_routes([
    aiohttp.web.get('/wsapi/in/', incoming_student_event.incoming_websocket_handler),
    aiohttp.web.get('/wsapi/out/', incoming_student_event.outgoing_websocket_handler)
])

# Handle AJAX event requests, incoming
app.add_routes([
    aiohttp.web.get('/webapi/event/', incoming_student_event.ajax_event_request),
    aiohttp.web.post('/webapi/event/', incoming_student_event.ajax_event_request),
    aiohttp.web.get('/webapi/courselist/', rosters.courselist_api),
    aiohttp.web.get('/webapi/courseroster/{course_id}', rosters.courseroster_api),
])

# Generic web-appy things
# Old version had: aiohttp.web.get('/', index),
app.add_routes([
    aiohttp.web.get('/favicon.ico', static_file_handler(paths.static("favicon.ico"))),
    aiohttp.web.get('/auth/login/{provider:google}', handler=auth_handlers.social),
    aiohttp.web.get('/auth/logout', handler=auth_handlers.logout),
    aiohttp.web.get('/auth/userinfo', handler=auth_handlers.user_info)
])

app.add_routes([
    aiohttp.web.get('/admin/status', handler=admin.system_status)
])

# This might look scary, but it's innocous. There are server-side
# configuration options which the client needs to know about. This
# gives those. At the very least, we want to be able to toggle the
# client-side up between running with a real server and a dummy static
# server, but in the future, we might want to include things like URIs
# for different services the client can talk to and similar.
#
# This URI should **not** be the same as the filename. We have two
# files, config.json is loaded if no server is running (dummy mode), and
# this is overridden by the live server.
app.add_routes([
    aiohttp.web.get(
        '/config.json',
        learning_observer.client_config.client_config_handler
    ),
])

# We'd like to be able to have the root page themeable, for non-ETS deployments
# This is a quick-and-dirty way to override the main page.
root_file = settings.settings.get("theme", {}).get("root_file", "webapp.html")
app.add_routes([
    aiohttp.web.get('/', static_file_handler(paths.static(root_file))),
])

# New-style modular dashboards
dashboards = learning_observer.module_loader.dashboards()
for dashboard in dashboards:
    print(dashboards[dashboard])
    app.add_routes([
        aiohttp.web.get(
            "/dashboards/" + dashboards[dashboard]['url'],
            handler=dashboards[dashboard]['function'])
    ])


cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})


def fernet_key(secret_string):
    '''
    Generate key for our cookie storage based on the `session_secret`
    in our config file.
    '''
    md5_hash = hashlib.md5()
    md5_hash.update(secret_string.encode('utf-8'))
    return md5_hash.hexdigest().encode('utf-8')


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

repos = learning_observer.module_loader.static_repos()
for gitrepo in repos:
    giturl = "/static/repos/{module}/{gitrepo}/{{branch}}/{{filename}}".format(
        module=repos[gitrepo]['module'],
        gitrepo=gitrepo
    )
    app.add_routes([
        aiohttp.web.get(
            giturl,
            handler=gitserve.aio_gitserve.git_handler_wrapper(
                paths.repo(gitrepo),
                cookie_prefix="SHA_" + gitrepo,
                prefix=repos[gitrepo].get("prefix", None),
                bare=repos[gitrepo].get("bare", False),)
        )
    ])
    # TODO: Change to reg-exp so we can handle subdirs. For reference:
    # app.router.add_get(
    # r'/browse/{branch:[^{}/]+}/{filename:[^{}]+}',
    # gitserve.aio_gitserve.git_handler_wrapper(
    #    gitrepo,
    #    prefix=PREFIX,
    #    cookie_prefix="content_"
    # )
    # )


aiohttp_session.setup(app, aiohttp_session.cookie_storage.EncryptedCookieStorage(
    fernet_key(settings.settings['aio']['session_secret']),
    max_age=settings.settings['aio']['session_max_age']))

app.middlewares.append(auth_handlers.auth_middleware)

print("Running!")
aiohttp.web.run_app(app, port=8888)
