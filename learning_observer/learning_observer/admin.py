'''
Administrative Views
====================

Views for monitoring overall system operation, and eventually, for
administering the system.
'''
import copy
import numbers
import psutil
import sys

import aiohttp
import aiohttp.web

import dash.development.base_component

import learning_observer.module_loader
from learning_observer.log_event import debug_log

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

    def clean_json(json_object):
        '''
        * Deep copy a JSON object
        * Convert list-like objects to lists
        * Convert dictionary-like objects to dicts
        * Convert functions to string representations
        '''
        if isinstance(json_object, str):
            return str(json_object)
        if isinstance(json_object, numbers.Number):
            return json_object
        if isinstance(json_object, dict):
            return {key: clean_json(value) for key, value in json_object.items()}
        if isinstance(json_object, list) or isinstance(json_object, tuple):
            return [clean_json(i) for i in json_object]
        if isinstance(json_object, learning_observer.stream_analytics.fields.Scope):
            # We could make a nicer representation....
            return str(json_object)
        if callable(json_object):
            return str(json_object)
        if json_object is None:
            return json_object
        if str(type(json_object)) == "<class 'module'>":
            return str(json_object)
        if isinstance(json_object, dash.development.base_component.Component):
            return f"Dash Component {json_object}"
        raise ValueError("We don't yet handle this type in clean_json: {} (object: {})".format(type(json_object), json_object))

    status = {
        "status": "Alive!",
        "resources": machine_resources(),
        "modules": {
            "course_aggregators": clean_json(learning_observer.module_loader.course_aggregators()),
            "reducers": clean_json(learning_observer.module_loader.reducers()),
            "static_repos": learning_observer.module_loader.static_repos(),
            "dash_pages": clean_json(learning_observer.module_loader.dash_pages()),
            "named_queries": clean_json(learning_observer.module_loader.named_queries())
        },
        "routes": routes(request.app)
    }

    debug_log(status)

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
