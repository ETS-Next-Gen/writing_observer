'''
Views for monitoring overall system operation, and eventually, for
administering the system.
'''
import copy

import psutil

import aiohttp

import learning_observer.module_loader


def admin(function):
    '''
    Dummy decorator to mark a view as an admin view.

    This should be wired back to an auth/auth framework.
    '''
    return function


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
