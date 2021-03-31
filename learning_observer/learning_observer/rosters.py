'''
This gives class roster information:

- What classes a teach administrates
- Which students are in a class.

We can either retrieve class rosters from:

- Google Classroom
- A text file on the disk (currently for testing, but later for
  small-scale deploys)

In the future, we might want:

- more integrations
- a database option
- an option to autocreate "guest" users (for unauthenticated deploys)

As well as the option for several sources in the same system, perhaps.
'''

import json
import sys

import aiohttp
import aiohttp.web

import learning_observer.settings as settings

import learning_observer.log_event as log_event
import learning_observer.paths as paths

COURSE_URL = 'https://classroom.googleapis.com/v1/courses'
ROSTER_URL = 'https://classroom.googleapis.com/v1/courses/{courseid}/students'


def clean_google_ajax_data(resp_json, key, sort_key, default=None):
    '''
    This cleans up / standardizes Google AJAX data. In particular:

    - We want to handle errors and empty lists better
    - We often don't want the whole response, but just one field (`key`)
    - We often want some default if that field is missing (`default`)
    - We often want the response sensibly sorted (`sort_key`)
    '''
    # Convert errors into appropriate codes for clients
    if 'error' in resp_json:
        return {'error': resp_json['error']}  # Typically, resp_json['error'] == 'UNAUTHENTICATED'

    # If we just want one field, retrieve it, and handle issues cleanly if the field is missing
    if key is not None:
        if key in resp_json:
            resp_json = resp_json[key]
        # This happens if e.g. no courses. Google seems to just return {}
        # instead of {'courses': []}
        else:
            return default

    # Sort the list
    if sort_key is not None:
        resp_json.sort(key=sort_key)

    return resp_json


async def synthetic_ajax(request, url, parameters={}, key=None, sort_key=None, default=None):
    '''
    Stub similar to google_ajax, but grabbing data from local files.

    This is helpful for testing, but it's even more helpful since
    Google is an amazingly unreliable B2B company, and this lets us
    develop without relying on them.

    At some point, we'll want to upgrade this to support small-scale
    deployments, with a directory tree such as e.g.:

    `course-rosters/[course_id].json`

    and

    `class-lists/[teacher_id].json`
    '''
    synthetic_data = {
        COURSE_URL: paths.data("courses.json"),
        ROSTER_URL: paths.data("students.json")
    }
    return clean_google_ajax_data(json.load(open(synthetic_data[url])), key, sort_key, default=default)


async def google_ajax(request, url, parameters={}, key=None, sort_key=None, default=None):
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
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        async with client.get(url.format(**parameters), headers=request["auth_headers"]) as resp:
            resp_json = await resp.json()
            log_event.log_ajax(url, resp_json, request)
            return clean_google_ajax_data(resp_json, key, sort_key, default=default)

if 'roster-data' not in settings.settings or 'source' not in settings.settings['roster-data']:
    print("Settings file needs a `roster-data` element with a `source` element")
    sys.exit(-1)
elif settings.settings['roster-data']['source'] == "synthetic":
    ajax = synthetic_ajax
elif settings.settings['roster-data']['source'] == "google-api":
    ajax = google_ajax
else:
    print("Settings file `roster-data` element should have `source` field set to either:")
    print("  synthetic     (retrieve roster data from static data files)")
    print("  google-api    (retrieve roster data from Google)")
    print("In the future, we may offer finer-grained options")
    sys.exit(-1)


async def courselist(request):
    '''
    List all of the courses a teacher manages
    '''
    course_list = await ajax(
        request,
        url=COURSE_URL,
        key='courses',
        sort_key=lambda x: x.get('name', 'ZZ'),
        default=[]
    )
    return course_list


async def courseroster(request, course_id):
    '''
    List all of the students in a class
    '''
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
    return aiohttp.web.json_response(await courselist(request))


async def courseroster_api(request):
    course_id = int(request.match_info['course_id'])
    return aiohttp.web.json_response(await courseroster(request, course_id))
