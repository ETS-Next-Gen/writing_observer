'''
Import analytics modules
'''


import collections
# import importlib
# import pkgutil
import sys

import pkg_resources


# This is set to true after we've scanned and loaded modules

LOADED = False

DASHBOARDS = collections.OrderedDict()
REDUCERS = []
THIRD_PARTY = {}
STATIC_REPOS = {}


def dashboards():
    '''
    Return a dictionary of all modules the system can render.
    '''
    load_modules()
    return DASHBOARDS


def reducers():
    '''
    Return a list of all event processors / reducers. Note that
    we can have multiple reducers for the same event type.
    '''
    load_modules()
    return REDUCERS


def third_party():
    '''
    Return a list of modules to download from 3rd party repos.

    We should eventually:

    - Handle version conflicts more gracefully (e.g. by allowing
      hashes of multiple compatible versions)
    - Support serving static files from e.g. S3 or similar
      services rather than our own server (e.g. by filling in
      references in modules where needed, or through settings in
      config.json)
    - Serving from CDNs (for deploys where we don't mind leaking
      user data; e.g. development)

    ... but not today.

    We don't want these modules committed to our repo due to size.
    '''
    load_modules()
    return THIRD_PARTY


def static_repos():
    '''
    We can serve static files for each module. These are served
    straight from `git`. In the future, we'd like to cache this.

    There's a little bit of complexity and nuance in how we'd
    like to manage branches.

    In deployment / operational settings:

    - We'll want to be careful about WHICH branch and commit we
    serve. We don't want students, teachers, or search engines
    navigating all versions willy nilly.
    - This is primarily a research platform. In research settings,
    we usually DO want to allow users to go to different versions.
    This is helpful for research replicability ("what version did
    Subject 42 see?"), for the social practice of research (e.g.
    show a collaborator a prototype, while using IRB-approved
    versions for coglabs), for experiments (e.g. show different
    versions to different students), etc.

    For now, this is set up around the *research* use-case: Being able
    to run coglabs, small pilots, and similar, used in controlled
    settings, without confidential items in repos.

    Note that since this is all open-source, hosting static files from
    a repo is *typically* *not* a security issue. It can be a usability
    issue, though (e.g. if users find an outdated link via a search
    engine).

    (Of course, YMMV. If you're hosting test items in a repo, then you
    want to be very careful about security)\
    '''
    load_modules()
    return STATIC_REPOS


def load_modules():
    '''
    Iterate through entry points to:
    - Find all Learning Observer modules installed
    - Load dashboards from each module
    - Load reducers from each module

    This is called before we ask for something from modules, but it
    only changes state on startup (for now -- we might revist later
    if we want to be more dynamic).
    '''
    # pylint: disable=W0603
    global LOADED
    if LOADED:
        return

    # Iterate through Learning Observer modules
    for entrypoint in pkg_resources.iter_entry_points("lo_modules"):
        module = entrypoint.load()
        # Human-friendly name for the module. Might have spaces, etc.
        try:
            print(module.NAME)
        except AttributeError:
            print("Module missing required NAME attribute: " + repr(module))

        # Load any teacher dashboards
        if hasattr(module, "DASHBOARDS"):
            for dashboard in module.DASHBOARDS:
                dashboard_id = "{module}.{submodule}".format(
                    module=entrypoint.name,
                    submodule=module.DASHBOARDS[dashboard]['submodule'],
                )
                DASHBOARDS[dashboard_id] = {
                    # Human-readable name
                    "name": "{module}: {dashboard}".format(
                        module=module.NAME,
                        dashboard=dashboard
                    ),
                    # Root URL
                    "url": "{module}/{submodule}/{url}".format(
                        module=entrypoint.name,
                        submodule=module.DASHBOARDS[dashboard]['submodule'],
                        url=module.DASHBOARDS[dashboard]['url']
                    ),
                    "function": module.DASHBOARDS[dashboard]['function']
                }
                print(dashboard)
        else:
            print("Module has no dashboards")

        # Load any state reducers / event processors
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

        # Load a list of static files our server will serve
        #
        # There's a lot to think through in terms of absolute paths,
        # conflicts, etc. perhaps another time.
        if hasattr(module, "THIRD_PARTY"):
            for library_filename in module.THIRD_PARTY:
                # If another module already wants this library, confirm
                # it's under the same hash
                if library_filename in THIRD_PARTY:
                    if THIRD_PARTY[library_filename]['hash'] != \
                       module.THIRD_PARTY[library_filename]['hash']:
                        print("Version conflict in 3rd party libs:")
                        print(library_filename)
                        print(module.THIRD_PARTY[library_filename])
                        print(THIRD_PARTY[library_filename])
                        sys.exit(-1)
                else:
                    THIRD_PARTY[library_filename] = {
                        'urls': [],
                        'hash': module.THIRD_PARTY[library_filename]['hash'],
                        'users': []
                    }
                THIRD_PARTY[library_filename]['users'].append(module.NAME)
                THIRD_PARTY[library_filename]['urls'].append(
                    module.THIRD_PARTY[library_filename]['url']
                )

        # How we do this is TBD
        # This might be a placeholder
        # Perhaps /[module]/[static]/[repo]/[branch]?
        if hasattr(module, "STATIC_FILE_GIT_REPOS"):
            STATIC_REPOS[entrypoint.name] = module.STATIC_FILE_GIT_REPOS

    print(THIRD_PARTY)
    LOADED = True
