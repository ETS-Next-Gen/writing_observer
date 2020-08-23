import aiohttp
import aiohttp.web

import settings

import log_event

COURSE_URL = 'https://classroom.googleapis.com/v1/courses'
ROSTER_URL = 'https://classroom.googleapis.com/v1/courses/{courseid}/students'


def clean_data(resp_json, key, sort_key, default=None):
    print("Response", resp_json)
    if 'error' in resp_json:
        return {'error': resp_json['error']}  # Typically, resp_json['error'] == 'UNAUTHENTICATED'
    if key is not None:
        if key in resp_json:
            resp_json = resp_json[key]
        # This happens if e.g. no courses. Google seems to just return {}
        # instead of {'courses': []}
        else:
            return default
    if sort_key is not None:
        resp_json.sort(key=sort_key)
    print(resp_json)
    return resp_json


async def synthetic_ajax(request, url, key=None, sort_key=None, default=None):
    '''
    Stub similar to google_ajax, but grabbing data from local files.

    This is helpful for testing, but it's even more helpful since
    Google is an amazingly unreliable B2B company, and this lets us
    develop without relying on them.
    '''
    synthetic_data = {
        COURSE_URL: "static_data/courses.json",
        ROSTER_URL: "static_data/students.json"
    }
    return clean_data(open(synthetic_data[url]).read(), default=default)


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
            return clean_data(resp_json, key, sort_key, default=default)


async def courselist(request):
    course_list = await google_ajax(
        request,
        url=COURSE_URL,
        key='courses',
        sort_key=lambda x: x.get('name', 'ZZ'),
        default=[]
    )
    return course_list


async def courseroster(request, course_id):
    roster = await google_ajax(
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
