'''
Administrative Views
====================

Views for monitoring overall system operation, and eventually, for
administering the system.
'''
import copy

import psutil

import aiohttp

import learning_observer.module_loader


def admin(func):
    '''
    Decorator to mark a view as an admin view.

    This should be moved to the auth/auth framework, and have more
    granular levels (e.g. teachers and sys-admins). We probably don't
    want a full ACL scheme (which overcomplicates things), but we will
    want to think through auth/auth.
    '''
    def f(request):
        if 'user' in request and \
           request['user'] is not None and \
           'authorized' in request['user'] and \
           request['user']['authorized']:
            return func(request)
        else:
            raise
    return f


def machine_resources():
    '''
    A dictionary of information about memory, CPU, etc. usage
    '''
    mountpoints = [p.mountpoint for p in psutil.disk_partitions()]
    disk_space = {p: psutil.disk_usage(p).percent for p in mountpoints}

    return {
        "usage": {
            "cpu_percent": psutil.cpu_percent(),
            "virtual_mem": psutil.virtual_memory().percent,
            "swap_memory": psutil.swap_memory().percent,
            "disk_space": disk_space
        }
    }


def routes(app):
    '''
    A list of routes. We compactify this quite a bit for pretty
    rendering in Firefox. If a client ever handles this, we might
    want to standardize this a bit more, though (it can return
    strings and dictionaries right now).
    '''
    resources = []
    for resource in app.router.resources():
        info = resource.get_info()
        if 'path' in info:
            resources.append(info['path'])
        elif 'formatter' in info:
            resources.append(info['formatter'])
        else:
            sinfo = {}
            for key in info:
                sinfo[key] = str(info[key])
            resources.append(sinfo)
    return resources


@admin
async def system_status(request):
    '''
    View for a system status screen. This shows:
    - Loaded modules
    - Available URLs
    - System resource usage

    This returns JSON, which renders very nicely in Firefox, but might
    be handled by a client-side app at some point. If that happens, we
    might change the API a bit to make it more computer-friendly and
    less Firefox-friendly.
    '''
    dashboards = copy.deepcopy(learning_observer.module_loader.dashboards())
    for k in dashboards:
        dashboards[k]['function'] = str(dashboards[k]['function'])
    reducers = copy.deepcopy(learning_observer.module_loader.reducers())
    for k in reducers:
        k['function'] = str(k['function'])

    return aiohttp.web.json_response({
        "status": "Alive!",
        "resources": machine_resources(),
        "modules": {
            "dashboards": dashboards,
            "reducers": reducers,
            "static_repos": learning_observer.module_loader.static_repos()
        },
        "routes": routes(request.app)
    })


@admin
async def die(request):
    '''
    Shut down the server.

    TODO: Replace this with a clean shutdown which closes all sockets,
    etc. But this still beats killing the process.
    '''
    sys.exit(-1)
    return aiohttp.web.json_response({'status': 'dead'})
