'''
Import analytics modules
'''


import collections
import importlib
import pkgutil
import pkg_resources

loaded = False

DASHBOARDS = collections.OrderedDict()
def dashboards():
    if not loaded:
        load_modules()
    return DASHBOARDS

REDUCERS = []
def reducers():
    if not loaded:
        load_modules()
    return REDUCERS

def load_modules():
    global loaded
    if loaded:
        return
    for entrypoint in pkg_resources.iter_entry_points("lo_modules"):
        module = entrypoint.load()
        try:
            print(module.NAME)
        except AttributeError:
            print("Module missing required NAME attribute: " + repr(module))
        if hasattr(module, "DASHBOARDS"):
            for dashboard in module.DASHBOARDS:
                dashboard_id = "{module}.{submodule}".format(
                    module = entrypoint.name,
                    submodule = module.DASHBOARDS[dashboard]['submodule'],
                )
                DASHBOARDS[dashboard_id] = {
                    # Human-readable name
                    "name": "{module}: {dashboard}".format(
                        module = module.NAME,
                        dashboard = dashboard
                    ),
                    # Root URL
                    "url": "{module}/{submodule}/{url}".format(
                        module = entrypoint.name,
                        submodule = module.DASHBOARDS[dashboard]['submodule'],
                        url = module.DASHBOARDS[dashboard]['url']
                    ),
                    "function": module.DASHBOARDS[dashboard]['function']
                }
                print(dashboard)
        else:
            print("Module has no dashboards")

        if hasattr(module, "REDUCERS"):
            for reducer in module.REDUCERS:
                print("Reducer: ", reducer)
                function = reducer['function']
                context = reducer['context']
                # reducer_id = "{module}.{name}".format(
                #     module=function.__module__,
                #     name=function.__name__
                # )
                REDUCERS.append({
                    "context": context,
                    "function": function
                })
        else:
            print("Module has no reducers")

    loaded = True
