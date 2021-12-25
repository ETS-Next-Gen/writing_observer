'''
Import analytics modules

This should run _after_ paths and settings
'''


import collections
import copy
# import importlib
# import pkgutil
import os.path
import sys

import pkg_resources

import gitserve.gitaccess

import learning_observer.paths
import learning_observer.settings

# This is set to true after we've scanned and loaded modules
LOADED = False

COURSE_AGGREGATORS = collections.OrderedDict()
REDUCERS = []
THIRD_PARTY = {}
STATIC_REPOS = {}
STUDENT_DASHBOARDS = []
COURSE_DASHBOARDS = []

# Additional calls, primarily for metadata
AJAX = {}


def extra_views():
    '''
    We used to just have dashboards rendered as views as a hack. This
    will use the same API, provide backwards-compatibility, but also
    act as a place for things which aren't dashboards. Modules ought
    to be able to define random views.

    To Be Implemented
    '''
    return []


def student_dashboards():
    '''
    URLs of per-student views
    '''
    load_modules()
    return STUDENT_DASHBOARDS


def course_dashboards():
    '''
    URLs of per-course views
    '''
    load_modules()
    return COURSE_DASHBOARDS


def course_aggregators():
    '''
    Return a dictionary of all modules the system can render.
    TODO: Rename to teacher aggregators or similar.
    '''
    load_modules()
    return COURSE_AGGREGATORS


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


def ajax():
    load_modules()
    return AJAX


def load_modules():
    '''
    Iterate through entry points to:
    - Find all Learning Observer modules installed
    - Load course_aggregators from each module
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
        if not hasattr(module, "NAME"):
            print("Module missing required NAME attribute: " + repr(module))
            print("Please give your module a short, human-friendly name")
            print("Spaces, etc. are okay")
            sys.exit(-1)

        print("Loading module: {pypackage} ({name})".format(
            name=module.NAME,
            pypackage=str(entrypoint),
            module=entrypoint.name
        ))

        # Load any teacher course_aggregators
        # TODO: These should be relabeled within modules.
        # are now pages which call these.
        if hasattr(module, "COURSE_AGGREGATORS"):
            for aggregator in module.COURSE_AGGREGATORS:
                aggregator_id = "{module}.{submodule}".format(
                    module=entrypoint.name,
                    submodule=aggregator
                )
                COURSE_AGGREGATORS[aggregator_id] = {}
                COURSE_AGGREGATORS[aggregator_id].update(module.COURSE_AGGREGATORS[aggregator])
                COURSE_AGGREGATORS[aggregator_id]['long_id'] = aggregator_id
                COURSE_AGGREGATORS[aggregator_id]['short_id'] = aggregator

            # for aggregator in module.COURSE_AGGREGATORS:
            #     aggregator_id = "{module}.{submodule}".format(
            #         module=entrypoint.name,
            #         submodule=module.COURSE_AGGREGATORS[aggregator]['submodule'],
            #     )
            #     COURSE_AGGREGATORS[aggregator_id] = {
            #         # Human-readable name
            #         "name": "{module}: {aggregator}".format(
            #             module=module.NAME,
            #             aggregator=aggregator
            #         ),
            #         # Root URL
            #         "url": "{module}/{submodule}/{url}".format(
            #             module=entrypoint.name,
            #             submodule=module.COURSE_AGGREGATORS[aggregator]['submodule'],
            #             url=module.COURSE_AGGREGATORS[aggregator]['url']
            #         ),
            #         "function": module.COURSE_AGGREGATORS[aggregator]['function']
            #     }
            #     print(aggregator)
        else:
            print("Module has no course aggregators")

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

        # Load additional AJAX calls
        if hasattr(module, "AJAX"):
            AJAX[entrypoint.name] = module.AJAX

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

        # These should have more metadata at some point (e.g. what
        # module they came from), but this is fine for now.
        if hasattr(module, "COURSE_DASHBOARDS"):
            COURSE_DASHBOARDS.extend(module.COURSE_DASHBOARDS)

        if hasattr(module, "STUDENT_DASHBOARDS"):
            STUDENT_DASHBOARDS.extend(module.COURSE_DASHBOARDS)

        # Clone module repos for serving static files, if we need to
        if hasattr(module, "STATIC_FILE_GIT_REPOS"):
            for repo in module.STATIC_FILE_GIT_REPOS:
                if repo in STATIC_REPOS:
                    print("{repo} appears twice".format(repo=repo))
                    print("This isn't bad, but isn't implemented yet.")
                    print("We want code to either make sure both versions")
                    print("are the same, or place them in different locations,")
                    print("or something. Please code that up and make a PR!")
                    sys.exit(-1)
                STATIC_REPOS[repo] = copy.deepcopy(module.STATIC_FILE_GIT_REPOS[repo])
                # TODO: This is a bit awkward.... The URL and key structure won't work well
                # if we use the same repo twice.
                STATIC_REPOS[repo]['module'] = entrypoint.name
                if not os.path.exists(learning_observer.paths.repo(repo)):
                    print("Repo {repo} does not exist.".format(repo=repo))
                    print("It is requested by {module}".format(module=entrypoint.name))
                    print("Should I clone it from {url} to {location}?".format(
                        location=learning_observer.paths.repo(repo),
                        url=module.STATIC_FILE_GIT_REPOS[repo]['url']
                    ))
                    yn = input("Yes/No> ")
                    if yn.lower().strip() not in ["y", "tak", "yes", "yup", "好", "نعم"]:
                        print("Fine. Get it yourself, and configure the location")
                        print("in the setting file under repos. Run me again once it's")
                        print("there.")
                        sys.exit(-1)
                    gitrepo = gitserve.gitaccess.GitRepo(learning_observer.paths.repo(repo))
                    print(gitrepo.clone(
                        module.STATIC_FILE_GIT_REPOS[repo]['url'],
                        mirror=module.STATIC_FILE_GIT_REPOS[repo].get("mirror", True)
                    ))
                # Paths are top-level for bare repos e.g. `/home/ubuntu/repo` and subdir for
                # working repos e.g. `/home/ubuntu/repo.git` which we need to later manage.
                if not os.path.exists(os.path.join(learning_observer.paths.repo(repo), ".git")):
                    STATIC_REPOS[repo]['bare'] = True
        print(STATIC_REPOS)
    LOADED = True
