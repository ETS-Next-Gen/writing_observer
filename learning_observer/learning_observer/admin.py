'''
Administrative Views
====================

Views for monitoring overall system operation, and eventually, for
administering the system.
'''
import copy
import numbers

import psutil

import aiohttp
import aiohttp.web

import learning_observer.module_loader

from learning_observer.auth.utils import admin


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

    def clean_json(js):
        '''
        * Deep copy a JSON object
        * Convert list-like objects to lists
        * Convert dictionary-like objects to dicts
        * Convert functions to string representations
        '''
        if isinstance(js, str):
            return str(js)
        elif isinstance(js, numbers.Number):
            return js
        elif isinstance(js, dict):
            return {key: clean_json(value) for key, value in js.items()}
        elif isinstance(js, list):
            return [clean_json(i) for i in js]
        elif callable(js):
            return str(js)
        else:
            print(js)
            print(type(js))
            raise ValueError("We don't yet handle this type")

    status = {
        "status": "Alive!",
        "resources": machine_resources(),
        "modules": {
            "course_aggregators": clean_json(learning_observer.module_loader.course_aggregators()),
            "reducers": clean_json(learning_observer.module_loader.reducers()),
            "static_repos": learning_observer.module_loader.static_repos()
        },
        "routes": routes(request.app)
    }

    print(status)

    return aiohttp.web.json_response(status)


@admin
async def die(request):
    '''
    Shut down the server.

    TODO: Replace this with a clean shutdown which closes all sockets,
    etc. But this still beats killing the process.
    '''
    sys.exit(-1)
    return aiohttp.web.json_response({
        'status': 'dead'  # Just like this code :)
    })
