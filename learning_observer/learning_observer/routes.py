'''
Map URLs to functions which handle them.
'''

import getpass
import os
import secrets
import sys

import aiohttp
import aiohttp.web

import gitserve.aio_gitserve

import learning_observer.admin as admin
import learning_observer.auth
import learning_observer.auth.http_basic
import learning_observer.client_config
import learning_observer.incoming_student_event as incoming_student_event
import learning_observer.dashboard
import learning_observer.rosters as rosters
import learning_observer.module_loader

import learning_observer.paths as paths
import learning_observer.settings as settings


from learning_observer.utility_handlers import *


def add_routes(app):
    '''
    Massive routine to set up all static routes.

    This should be broken out into routines for each group of routes,
    or handled as a data file, or similar.
    '''
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
        aiohttp.web.get(
            '/wsapi/dashboard',
            learning_observer.dashboard.websocket_dashboard_view),
        aiohttp.web.get(
            '/webapi/course_dashboards',
            ajax_handler_wrapper(learning_observer.module_loader.course_dashboards)),
        aiohttp.web.get(
            '/webapi/student_dashboards',
            ajax_handler_wrapper(learning_observer.module_loader.student_dashboards))
    ])

    app.add_routes([
        aiohttp.web.get(
            '/wsapi/generic_dashboard',
            learning_observer.dashboard.generic_dashboard)
    ])

    # Serve static files
    app.add_routes([
        aiohttp.web.get(
            '/static/{filename}',
            static_directory_handler(paths.static())),
        aiohttp.web.get(
            '/static/modules/{filename}',
            static_directory_handler(paths.static("modules"))),

        # TODO: Make consistent. 3rdparty versus 3rd_party and maybe clean up URLs.
        aiohttp.web.get(
            r'/static/repos/{module:[^{}/]+}/{repo:[^{}/]+}/{branch:[^{}/]+}/3rdparty/{filename:[^{}]+}',
            static_directory_handler(paths.static("3rd_party"))),
        aiohttp.web.get(
            '/static/3rd_party/{filename}',\
            static_directory_handler(paths.static("3rd_party"))),
        aiohttp.web.get(
            '/static/media/{filename}',
            static_directory_handler(paths.static("media"))),
        aiohttp.web.get(
            '/static/media/avatar/{filename}',
            static_directory_handler(paths.static("media/hubspot_persona_images/"))),
    ])

    # Handle web sockets event requests, incoming and outgoing
    app.add_routes([
        aiohttp.web.get(
            '/wsapi/in/',
            incoming_student_event.incoming_websocket_handler)
    ])

    # Handle AJAX event requests, incoming
    app.add_routes([
        aiohttp.web.get(
            '/webapi/event/',
            incoming_student_event.ajax_event_request),
        aiohttp.web.post(
            '/webapi/event/',
            incoming_student_event.ajax_event_request),
        aiohttp.web.get(
            '/webapi/courselist/',
            rosters.courselist_api),
        aiohttp.web.get(
            '/webapi/courseroster/{course_id}',
            rosters.courseroster_api),
    ])

    # Generic web-appy things
    app.add_routes([
        aiohttp.web.get(
            '/favicon.ico',
            static_file_handler(paths.static("favicon.ico"))),
        aiohttp.web.get(
            '/auth/logout',
            handler=learning_observer.auth.logout_handler),
        aiohttp.web.get(
            '/auth/userinfo',
            handler=learning_observer.auth.user_info_handler)
    ])

    if 'google-oauth' in settings.settings['auth']:
        print("Running with Google authentication")
        app.add_routes([
            aiohttp.web.get(
                '/auth/login/{provider:google}',
                handler=learning_observer.auth.social_handler),
        ])

    if 'password-file' in settings.settings['auth']:
        print("Running with password authentication")
        if not os.path.exists(settings.settings['auth']['password-file']):
            print("Configured to run with password file,"
                  "but no password file exists")
            print()
            print("Please either:")
            print("* Remove auth/password-file from the settings file")
            print("* Create a file {fn} with lo_passwd.py".format(
                fn=settings.settings['auth']['password-file']
            ))
            print("Typically:")
            print("python util/lo_passwd.py "
                  "--username {username} --password {password} "
                  "--filename {fn}".format(
                      username=getpass.getuser(),
                      password=secrets.token_urlsafe(16),
                      fn=settings.settings['auth']['password-file']
                  ))
            sys.exit(-1)
        app.add_routes([
            aiohttp.web.post(
                '/auth/login/password',
                learning_observer.auth.password_auth(
                    settings.settings['auth']['password-file'])
            )])

    # If we want to support multiple modes of authentication, including
    # http-basic, we can configure a URL in nginx which will require
    # http basic auth, which is used to log in, and then redirects back
    # home.
    if learning_observer.auth.http_basic.http_auth_page_enabled():
        # If we don't have a password file, we shouldn't have an auth page.
        # At the very least, the user should explicitly set it to `null`
        # if they are planning on using nginx for auth
        print("Enabling http basic auth page")
        auth_file = settings.settings['auth']['http-basic']["password-file"]
        app.add_routes([
            aiohttp.web.get(
                '/auth/login/http-basic',
                learning_observer.auth.http_basic.http_basic_auth(
                    filename=auth_file,
                    response=lambda:aiohttp.web.HTTPFound(location="/")
                )
            )
        ])

    # General purpose status page:
    # - List URLs
    # - Show system resources
    # Etc.
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

    # We'd like to be able to have the root page themeable, for
    # non-ETS deployments. This is a quick-and-dirty way to override
    # the main page.
    root_file = settings.settings.get("theme", {}).get("root_file", "webapp.html")
    app.add_routes([
        aiohttp.web.get('/', static_file_handler(paths.static(root_file))),
    ])

    # E.g. We have an alias of /static/common to /common
    # We place useful things modules can use, such as e.g. our logger
    app.add_routes([
        aiohttp.web.get('/common/{filename}', static_directory_handler(paths.static("common"))),
    ])

    # New-style modular views
    # extra_views = learning_observer.module_loader.extra_views()
    # for view in extra_views:
    #     print(extra_views[view])
    #     app.add_routes([
    #         # TODO: Change URL
    #         # TODO: Add classroom ID within URL
    #         # TODO: Add student API
    #         aiohttp.web.get(
    #             "/views/" + extra_views[view]['url'],
    #             handler=extra_views[view]['function'])
    #     ])

    # Allow AJAX calls.  Right now, the function receives a `request`
    # object. This should be cleaned in some way.
    ajax = learning_observer.module_loader.ajax()
    for module in ajax:
        for call in ajax[module]:
            path = "/ajax/{module}/{call}".format(module=module, call=call)
            print(path)
            app.add_routes([
                aiohttp.web.get(
                    path,
                    lambda x: aiohttp.web.json_response(ajax[module][call](x))
                )
            ])

    # Repos
    repos = learning_observer.module_loader.static_repos()
    for gitrepo in repos:
        giturl = r'/static/repos/' + repos[gitrepo]['module'] + '/' + gitrepo + '/{branch:[^{}/]+}/{filename:[^{}]+}'

        working_tree = paths.repo_debug_working_hack(gitrepo)  # Ignore the branch; serve from working tree
        bare = repos[gitrepo].get("bare", False)
        if working_tree:
            bare = False

        app.add_routes([
            aiohttp.web.get(
                giturl,
                handler=gitserve.aio_gitserve.git_handler_wrapper(
                    paths.repo(gitrepo),
                    cookie_prefix="SHA_" + gitrepo,
                    prefix=repos[gitrepo].get("prefix", None),
                    bare=bare,
                    working_tree_dev=working_tree)
            )
        ])
