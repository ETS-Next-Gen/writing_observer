'''
Class Roster Subsystem
======================

This gives class roster information:

- What classes a teach administrates
- Which students are in a class.

We can either retrieve class rosters from:

- Google Classroom                      (config setting: 'google')
- Text files on the disk for testing.   (config setting: 'test')
  We have two files:
  - courses.json
  - students.json
- A file hierarchy, for small-scale deploys.  ('filesystem')
- In progress: All students, for e.g. coglabs, experiments, and
  similar  ('all')

In the future, we might want:

- more integrations
- a database option
- an option to autocreate "guest" users (for unauthenticated deploys)

As well as the option for several sources in the same system, perhaps.

This file could be cleaned up a lot. Right now, we do a lot of this by
mock calls to Google AJAX. It also contains a large number of hacks which
we use to manage the data and to address variations in the roster sources
whether we are taking them from google or from our own backup data.

As of now this partially implements a separation between the internal ID
which shows up in our rosters as id or `user_id` and the id used for the
external sources of data.  We store external ids on student data under
external_ids and keep space for ids from google etc.  However as of now
we do not make use of it.  Ultimately it would be ideal to move so that
remote data retreival and raw document storage are done under an internal
id with this translation taking place at event storage time *or* that the
event retreival by the dashboard makes use of the external ids consistently
at composition time.  The latter approach however has the cost that we would
be redoing the lookup and indexing each time we pull the raw data. This has
the potential to create some extra, though probably manageable, queries.

In either case we get around it now by also adding in a cheap hack that
makes the internal ID for google-sourced users match the google ID. This
will need to change in a stable way for future use.

Note that these APIs and file locations aren't finished. In the future,
we may:

* Switch from .json to .yaml
* Have a less Googley format

As it stands this file is also part of the way through a naming refactor.
The roster information has changed from camel-case to underscores. The
actual group information has not. That should also be remapped and tested
so that class info uses the same format but that is scut work for another
time.
'''

import json
import os.path

import aiohttp
import aiohttp.web

import pathvalidate
import pss

import learning_observer.auth as auth
import learning_observer.cache
import learning_observer.constants as constants
import learning_observer.google
import learning_observer.kvs
import learning_observer.log_event as log_event
from learning_observer.log_event import debug_log
import learning_observer.paths as paths
import learning_observer.prestartup
import learning_observer.runtime
import learning_observer.settings as settings
import learning_observer.communication_protocol.integration


COURSE_URL = 'https://classroom.googleapis.com/v1/courses'
ROSTER_URL = 'https://classroom.googleapis.com/v1/courses/{courseid}/students'

pss.parser('roster_source', parent='string', choices=['google_api', 'all', 'test', 'filesystem'])
pss.register_field(
    name='source',
    type='roster_source',
    description='Source to use for student class rosters. This can be\n'\
                '`all`: aggregate all available students into a single class\n'\
                '`test`: use sample course and student files\n'\
                '`filesystem`: read rosters defined on filesystem\n'\
                '`google_api`: fetch from Google API',
    required=True
)


def clean_google_ajax_data(resp_json, key, sort_key, default=None, source=None):
    '''
    This cleans up / standardizes Google AJAX data. In particular:

    - We want to handle errors and empty lists better
    - We often don't want the whole response, but just one field (`key`)
    - We often want some default if that field is missing (`default`)
    - We often want the response sensibly sorted (`sort_key`)
    '''
    # Convert errors into appropriate codes for clients
    # Typically, resp_json['error'] == 'UNAUTHENTICATED'
    if 'error' in resp_json:
        return {'error': resp_json['error']}

    # Google sometimes returns results nested one extra level.
    #
    # If we just want one field, retrieve it, and handle issues cleanly
    # if the field is missing
    if key is not None:
        if key in resp_json:
            resp_json = resp_json[key]
        # This happens if e.g. no courses. Google seems to just return {}
        # instead of {'courses': []}
        else:
            return default

    # Convert all camel cases to underscores.
    util.translate_json_keys(resp_json, learning_observer.google.GOOGLE_TO_SNAKE)

    # Update the ID's to include the gc- prefix and to handle the external data.
    # this only runs if the quesry of concern was students meaning that we will
    # have a list of student dicts in resp_json.
    if (key == 'students'):
        adjust_external_gc_ids(resp_json)

    # Sort the list
    if sort_key is not None:
        resp_json.sort(key=sort_key)

    return resp_json


def adjust_external_gc_ids(resp_json):
    '''
    What we are concerned with here is handling cases where the id supplied by the
    google roster is a numerical value but we need to have gc- preprended to it
    for data fetching.  This is a relatively minor task but necessary for interfacing
    with the external data sources but makes it easier to get the stored values.

    This will be run qith 'students' requests meaning that the attached will be
    a possibly-empty? list of student dicts.

    This exists for the sole purpose of adjusting the internal ids and includes a
    cheap hack below that maps the internal user_id to match the google id.  Going
    forward that will need to be changed to something more robust. See the comments
    at the top of this module.
    '''

    # Iterate over the students performing an addition of the external_ids and possible
    # conversion of the individual id.
    for student_json in resp_json:

        # Pull the actual profile data.
        student_profile = student_json['profile']

        # Calculate the new ID to use for our student.
        google_id = auth.google_id_to_user_id(student_profile['id'])

        # As a cheap hack lets change the ids to match
        # student_profile[constants.USER_ID] = google_id
        #
        # This hack changes the internal ID which we then use for
        # document retreival.  Going forward it should not be done
        # this way and it would be better for us to make this use
        # the externals.
        student_json[constants.USER_ID] = google_id

        # For the present there is only one external id so we will add that directly.
        ext_ids = [{"source": "google", "id": google_id}]
        student_profile['external_ids'] = ext_ids


async def all_students():
    '''
    This crawls all of the keys in the KVS, and creates a list of all
    student IDs in redis. This should not be used in any form of
    large-scale production.
    '''
    keys = await learning_observer.kvs.KVS().keys()
    # Reduce list length by 2
    internal_keys = [k for k in keys if k.startswith("Internal")]

    # Pick out the STUDENT field, and place those in a list. This list should
    # have length 1 (if the field is there) or 0 (if it is not).
    student_field_lists = [[f for f in k.split(",") if f.startswith("STUDENT:")] for k in internal_keys]

    # Drop invalid keys, as well as ones which don't have a student field.
    #
    # For the remaining ones -- ones with a student ID -- just pick out the student ID.
    user_ids = [k[0].split(":")[1] for k in student_field_lists if len(k) == 1]

    # Drop duplicates
    return sorted(set(user_ids))


async def all_ajax(
        request, url,
        parameters=None, key=None, sort_key=None, default=None):
    '''
    Stub in information normally requested through Google's API,
    using a dummy course and all students in the system as the
    roster for that course.
    '''
    if url == COURSE_URL:
        return [{
            "id": "12345678901",
            "name": "All Students",
            "description_heading": "For easy small-scale deploys",
            "alternate_link": "https://www.ets.org/",
            "teacher_group_email": "",
            "course_group_email": "",
            "teacher_folder": {
                "id": "",
                "title": "All Students",
                "alternate_link": ""
            },
            "calendar_id": "NA"
        }]
    if url == ROSTER_URL:
        students = await all_students()

        def profile(student, index):
            idnum = str(index + 100)
            # We'll created a name from the ID passed
            name = '-'.join(student.split('-')[2:]).replace("%23", "")
            return {
                constants.USER_ID: student,
                "profile": {
                    "name": {
                        "given_name": name,
                        "family_name": idnum,
                        "full_name": name
                    },
                    "emailAddress": "student" + idnum + "@localhost",
                    "photoUrl": "//",
                    "external_ids": []
                }
            }

        return [profile(s, i) for (s, i) in zip(students, range(len(students)))]
    # Otherwise, we need to code up the other URLs
    raise AttributeError("Unknown Google URL: " + url)


async def synthetic_ajax(
        request, url,
        parameters=None, key=None, sort_key=None, default=None):
    '''
    Stub similar to google_ajax, but grabbing data from local files.

    This is helpful for testing, but it's even more helpful since
    Google is an amazingly unreliable B2B company, and this lets us
    develop without relying on them.
    '''
    roster_source = settings.pss_settings.source(types=['roster_data'])
    if roster_source == 'test':
        synthetic_data = {
            COURSE_URL: paths.data("courses.json"),
            ROSTER_URL: paths.data("students.json")
        }
    elif roster_source == 'filesystem':
        debug_log(request[constants.USER])
        safe_userid = pathvalidate.sanitize_filename(request[constants.USER][constants.USER_ID])
        courselist_file = "courselist-" + safe_userid
        if parameters is not None and 'courseid' in parameters:
            safe_courseid = pathvalidate.sanitize_filename(str(parameters['courseid']))
            roster_file = "courseroster-" + safe_courseid
        else:
            roster_file = "default"
        synthetic_data = {
            ROSTER_URL: paths.data("course_rosters/{roster_file}.json".format(
                roster_file=roster_file)),
            COURSE_URL: paths.data("course_lists/{courselist_file}.json".format(
                courselist_file=courselist_file))
        }
    else:
        debug_log("Roster data source is not recognized:", roster_source)
        raise ValueError("Roster data source is not recognized: {}".format(roster_source)
                         + " (should be 'test' or 'filesystem')")
    try:
        data = json.load(open(synthetic_data[url]))
    except FileNotFoundError as exc:
        debug_log(exc)
        raise aiohttp.web.HTTPInternalServerError(
            text="Server configuration error. "
            "No course roster file for your account. "
            "Please ask the sysadmin to make one. "
            "(And yes, they'll want to know about this issue;"
            "you won't be bugging them)"
        )
    return data


async def google_ajax(
        request, url,
        parameters=None, key=None, sort_key=None, default=None):
    '''
    Request information through Google's API

    Most requests return a dictionary with one key. If we just want
    that element, set `key` to be the element of the dictionary we want

    This is usually a list. If we want to sort this, pass a function as
    `sort_key`

    Note that we return error as a json object with error information,
    rather than raising an exception. In most cases, we want to pass
    this error back to the JavaScript client, which can then handle
    loading the auth page.
    '''
    if parameters is None:  # {} should NOT be a default param. See W0102.
        parameters = {}
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        # We would like better error handling for what to do if auth_headers
        # is not set. However, we haven't figured out a better thing to do.
        # We saw this happen due to a bug, but similar bugs might come up
        # in the future (we forgot to propagate the headers from the
        # session).
        async with client.get(url.format(**parameters), headers=request[constants.AUTH_HEADERS]) as resp:
            resp_json = await resp.json()
            log_event.log_ajax(url, resp_json, request)
            return clean_google_ajax_data(
                resp_json, key, sort_key, default=default
            )

ajax = None


@learning_observer.prestartup.register_startup_check
def init():
    '''
    * Set up the ajax function.
    * Check that the settings are valid.
    * Check that the roster data paths exist.

    TODO: It should be broken out into a separate check function and init function,
    or smaller functions otherwise.
    '''
    global ajax
    roster_source = settings.pss_settings.source(types=['roster_data'])
    if 'roster_data' not in settings.settings:
        print(settings.settings)
        raise learning_observer.prestartup.StartupCheck(
            "Settings file needs a `roster_data` element with a `source` element. No `roster_data` element found."
        )
    elif 'source' not in settings.settings['roster_data']:
        raise learning_observer.prestartup.StartupCheck(
            "Settings file needs a `roster_data` element with a `source` element. No `source` element found."
        )
    elif roster_source in ['test', 'filesystem']:
        ajax = synthetic_ajax
    elif roster_source in ["google_api"]:
        ajax = google_ajax
    elif roster_source in ["all"]:
        ajax = all_ajax
    else:
        raise learning_observer.prestartup.StartupCheck(
            "Settings file `roster_data` element should have `source` field\n"
            "set to either:\n"
            "  test        (retrieve from files courses.json and students.json)\n"
            "  google_api  (retrieve roster data from Google)\n"
            "  filesystem  (retrieve roster data from file system hierarchy\n"
            "  all  (retrieve roster data as all students)"
        )
    REQUIRED_PATHS = {
        'test': [
            paths.data("students.json"),
            paths.data("courses.json")
        ],
        'filesystem': [
            paths.data("course_lists/"),
            paths.data("course_rosters/")
        ]
    }

    if roster_source in REQUIRED_PATHS:
        r_paths = REQUIRED_PATHS[roster_source]
        for p in r_paths:
            if not os.path.exists(p):
                raise learning_observer.prestartup.StartupCheck(
                    "Missing course roster files!\n"
                    "The following are required:\t{paths}\n\n"
                    "If you plan to use rosters from local files, please run:\n"
                    "{commands}\n\n"
                    "(And ideally, they'll be populated with\n"
                    "a list of courses, and of students for\n"
                    "those courses)\n\n"
                    "If you plan to use other sources of roster,\n"
                    "data please change creds.yaml instead".format(
                        paths=", ".join(r_paths),
                        commands="\n".join(["mkdir {path}".format(path=path) for path in r_paths])
                    )
                )

    return ajax


async def courselist(request):
    '''
    List all of the courses a teacher manages: Helper
    '''
    # New code
    if settings.pss_settings.source(types=['roster_data']) in ["google_api"]:
        runtime = learning_observer.runtime.Runtime(request)
        return await learning_observer.google.courses(runtime)

    # Legacy code
    course_list = await ajax(
        request,
        url=COURSE_URL,
        key='courses',
        sort_key=lambda x: x.get('name', 'ZZ'),
        default=[]
    )
    return course_list


async def courseroster_runtime(runtime, course_id):
    '''
    Wrapper to call courseroster with a runtime object
    '''
    return await courseroster(runtime.get_request(), course_id)


@learning_observer.communication_protocol.integration.publish_function('learning_observer.courseroster')
async def memoize_courseroster_runtime(runtime, course_id):
    '''Wrapper function for calling the course roster with runtime from
    within the communication protocol. This is so we can memoize the
    result without modifying the behavior of `courseroster_runtime`
    when used outside of the communication protocol.

    TODO this node should only be ran once in the communication protocol.
    For now, we use memoization to limit how often this node is called.
    In the future, we ought to be able to specify how the values from
    individual nodes are handled: static, dynamic (current), or memoized.
    '''
    @learning_observer.cache.async_memoization()
    async def memoization_layer(c):
        return await courseroster_runtime(runtime, c)
    return await memoization_layer(course_id)


async def courseroster(request, course_id):
    '''
    List all of the students in a course: Helper
    '''
    if settings.pss_settings.source(types=['roster_data']) in ["google_api"]:
        runtime = learning_observer.runtime.Runtime(request)
        return await learning_observer.google.roster(runtime, courseId=course_id)

    roster = await ajax(
        request,
        url=ROSTER_URL,
        parameters={'courseid': int(course_id)},
        key='students',
        sort_key=lambda x: x.get('name', {}).get('fullName', 'ZZ'),
        default=[]
    )
    return roster


async def courselist_api(request):
    '''
    List all of the courses a teacher manages: Handler
    '''
    return aiohttp.web.json_response(await courselist(request))


async def courseroster_api(request):
    '''
    List all of the students in a course: Handler
    '''
    course_id = int(request.match_info['course_id'])
    return aiohttp.web.json_response(await courseroster(request, course_id))
