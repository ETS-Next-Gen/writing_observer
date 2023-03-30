'''
We will gradually move all of the Google-specific code into here.

Our design goals:
- Easily call into Google APIs (Classroom, Drive, Docs, etc.)
- Be able to preprocess the data into standard formats

On a high level, for each Google request, we plan to have a 4x4 grid:
- Web request and function call
- Cleaned versus raw data

The Google APIs are well-designed (if poorly-documented, and with occasional
bugs), but usually return more data than we need, so we have cleaner functions.

For a given call, we might have several cleaners. For example, for a Google Doc,
Google returns a massive JSON object containing everything. For most purposes,
we don't need all of that, and it's more convenient to work with a plain
text representation, and for downstream code to not need to understand this
JSON. However, for some algorithms, we might need additonal data of different
sorts. It's still more convenient to hand this back in something simplified for
analysis.
'''

import collections
import itertools
import json
import recordclass
import string
import re

import aiohttp
import aiohttp.web

import learning_observer.settings as settings
import learning_observer.log_event
import learning_observer.util
import learning_observer.auth
import learning_observer.runtime


cache = None


GOOGLE_FIELDS = [
    'alternateLink', 'calculationType', 'calendarId', 'courseGroupEmail',
    'courseId', 'courseState', 'creationTime', 'descriptionHeading',
    'displaySetting', 'emailAddress', 'enrollmentCode', 'familyName',
    'fullName', 'givenName', 'gradebookSettings', 'guardiansEnabled',
    'ownerId', 'photoUrl', 'teacherFolder', 'teacherGroupEmail', 'updateTime',
    'userId'
]

# On in-take, we want to convert Google's CamelCase to LO's snake_case. This
# dictionary contains the conversions.
camel_to_snake = re.compile(r'(?<!^)(?=[A-Z])')
GOOGLE_TO_SNAKE = {field: camel_to_snake.sub('_', field).lower() for field in GOOGLE_FIELDS}


# These took a while to find, but many are documented here:
# https://developers.google.com/drive/api/v3/reference/
# This list might change. Many of these contain additional (optional) parameters
# which we might add later. This is here for debugging, mostly. We'll stabilize
# APIs later.
class Endpoint(recordclass.make_dataclass("Endpoint", ["name", "remote_url", "doc", "cleaners"], defaults=["", None])):
    def arguments(self):
        return extract_parameters_from_format_string(self.remote_url)

    def _local_url(self):
        parameters = "}/{".join(self.arguments())
        base_url = f"/google/{self.name}"
        if len(parameters) == 0:
            return base_url
        else:
            return base_url + "/{" + parameters + "}"

    def _add_cleaner(self, name, cleaner):
        if self.cleaners is None:
            self.cleaners = dict()
        self.cleaners[name] = cleaner
        if 'local_url' not in cleaner:
            cleaner['local_url'] = self._local_url + "/" + name

    def _cleaners(self):
        if self.cleaners is None:
            return []
        else:
            return self.cleaners


ENDPOINTS = list(map(lambda x: Endpoint(*x), [
    ("document", "https://docs.googleapis.com/v1/documents/{documentId}"),
    ("course_list", "https://classroom.googleapis.com/v1/courses"),
    ("course_roster", "https://classroom.googleapis.com/v1/courses/{courseId}/students"),
    ("course_work", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork"),
    ("coursework_submissions", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork/{courseWorkId}/studentSubmissions"),
    ("coursework_materials", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWorkMaterials"),
    ("course_topics", "https://classroom.googleapis.com/v1/courses/{courseId}/topics"),
    ("drive_files", "https://www.googleapis.com/drive/v3/files"),    # This paginates. We only return page 1.
    ("drive_about", "https://www.googleapis.com/drive/v3/about?fields=%2A"),  # Fields=* probably gives us more than we need
    ("drive_comments", "https://www.googleapis.com/drive/v3/files/{documentId}/comments?fields=%2A&includeDeleted=true"),
    ("drive_revisions", "https://www.googleapis.com/drive/v3/files/{documentId}/revisions")
]))


def extract_parameters_from_format_string(format_string):
    '''
    Extracts parameters from a format string. E.g.

    >>> ("hello {hi} my {bye}")]
    ['hi', 'bye']
    '''
    # The parse returns a lot of context, which we discard. In particular, the
    # last item is often about the suffix after the last parameter and may be
    # `None`
    return [f[1] for f in string.Formatter().parse(format_string) if f[1] is not None]


async def raw_google_ajax(runtime, target_url, **kwargs):
    '''
    Make an AJAX call to Google, managing auth + auth.

    * runtime is a Runtime class containing request information.
    * default_url is typically grabbed from ENDPOINTS
    * ... and we pass the named parameters
    '''
    if isinstance(runtime, learning_observer.runtime.Runtime):
        request = runtime.get_request()
    else:
        request = runtime
    url = target_url.format(**kwargs)
    cache_key = "raw_google/" + learning_observer.util.url_pathname(url)
    if settings.feature_flag('use_google_ajax') is not None:
        value = await cache[cache_key]
        if value is not None:
            return learning_observer.util.translate_json_keys(
                json.loads(value),
                GOOGLE_TO_SNAKE
            )
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        if 'auth_headers' not in request:
            raise aiohttp.web.HTTPUnauthorized(text="Please log in")  # TODO: Consistent way to flag this
        async with client.get(url, headers=request["auth_headers"]) as resp:
            response = await resp.json()
            learning_observer.log_event.log_ajax(target_url, response, request)
            if settings.feature_flag('use_google_ajax') is not None:
                await cache.set(cache_key, json.dumps(response, indent=2))
            return learning_observer.util.translate_json_keys(
                response,
                GOOGLE_TO_SNAKE
            )


def raw_access_partial(remote_url, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    Google APIs.

    To test this, try:

        print(await raw_document(request, documentId="some_google_doc_id"))
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to Google
        '''
        return await raw_google_ajax(request, remote_url, **kwargs)
    setattr(caller, "__qualname__", name)

    return caller


def initialize_and_register_routes(app):
    '''
    This is a big 'ol function which might be broken into smaller ones at some
    point. We:

    - Created debug routes to pass through AJAX requests to Google
    - Created production APIs to have access to cleaned versions of said data
    - Create local function calls to call from other pieces of code
      within process

    We probably don't need all of this in production, but a lot of this is
    very important for debugging. Having APIs is more useful than it looks, since
    making use of Google APIs requires a lot of infrastructure (registering
    apps, auth/auth, etc.) which we already have in place on dev / debug servers.
    '''
    # For now, all of this is behind one big feature flag. In the future,
    # we'll want seperate ones for the debugging tools and the production
    # staff
    if 'google_routes' not in settings.settings['feature_flags']:
        return

    for key in ['save_google_ajax', 'use_google_ajax', 'save_clean_ajax', 'use_clean_ajax']:
        if key in settings.settings['feature_flags']:
            global cache
            cache = learning_observer.kvs.FilesystemKVS(path=learning_observer.paths.data('google'), subdirs=True)

    # Provide documentation on what we're doing
    app.add_routes([
        aiohttp.web.get("/google", api_docs_handler)
    ])

    def make_ajax_raw_handler(remote_url):
        '''
        This creates a handler to forward Google requests to the client. It's used
        for debugging right now. We should think through APIs before relying on this.
        '''
        async def ajax_passthrough(request):
            '''
            And the actual handler....
            '''
            response = await raw_google_ajax(
                request,
                remote_url,
                **request.match_info
            )

            return aiohttp.web.json_response(response)
        return ajax_passthrough

    def make_cleaner_handler(raw_function, cleaner_function, name=None):
        async def cleaner_handler(request):
            '''
            '''
            response = cleaner_function(
                await raw_function(request, **request.match_info)
            )
            if isinstance(response, dict) or isinstance(response, list):
                return aiohttp.web.json_response(
                    response
                )
            elif isinstance(response, str):
                return aiohttp.web.Response(
                    text=response
                )
            else:
                raise AttributeError(f"Invalid response type: {type(response)}")
        if name is not None:
            setattr(cleaner_handler, "__qualname__", name + "_handler")

        return cleaner_handler

    def make_cleaner_function(raw_function, cleaner_function, name=None):
        async def cleaner_local(request, **kwargs):
            google_response = await raw_function(request, **kwargs)
            clean = cleaner_function(google_response)
            return clean
        if name is not None:
            setattr(cleaner_local, "__qualname__", name)
        return cleaner_local

    for e in ENDPOINTS:
        function_name = f"raw_{e.name}"
        raw_function = raw_access_partial(remote_url=e.remote_url, name=e.name)
        globals()[function_name] = raw_function
        cleaners = e._cleaners()
        for c in cleaners:
            app.add_routes([
                aiohttp.web.get(
                    cleaners[c]['local_url'],
                    make_cleaner_handler(
                        raw_function,
                        cleaners[c]['function'],
                        name=cleaners[c]['name']
                    )
                )
            ])
            globals()[cleaners[c]['name']] = make_cleaner_function(
                raw_function,
                cleaners[c]['function'],
                name=cleaners[c]['name']
            )
        app.add_routes([
            aiohttp.web.get(
                e._local_url(),
                make_ajax_raw_handler(e.remote_url)
            )
        ])


def api_docs_handler(request):
    '''
    Return a list of available endpoints.

    Eventually, we should also document available function calls
    '''
    response = "URL Endpoints:\n\n"
    for endpoint in ENDPOINTS:
        response += f"{endpoint._local_url()}\n"
        cleaners = endpoint._cleaners()
        for c in cleaners:
            response += f"   {cleaners[c]['local_url']}\n"
    response += "\n\n Globals:"
    if False:
        response += str(globals())
    return aiohttp.web.Response(text=response)


def register_cleaner(data_source, cleaner_name):
    '''
    This will register a cleaner function, for export both as a web service
    and as a local function call.
    '''
    def decorator(f):
        found = False
        for endpoint in ENDPOINTS:
            if endpoint.name == data_source:
                found = True
                endpoint._add_cleaner(
                    cleaner_name,
                    {
                        'function': f,
                        'local_url': f'{endpoint._local_url()}/{cleaner_name}',
                        'name': cleaner_name
                    }
                )

        if not found:
            raise AttributeError(f"Data source {data_source} invalid; not found in endpoints.")
        return f

    return decorator


# Rosters
@register_cleaner("course_roster", "roster")
def clean_course_roster(google_json):
    '''
    Retrieve the roster for a course, alphabetically
    '''
    students = google_json.get('students', [])
    students.sort(
        key=lambda x: x.get('name', {}).get('fullName', 'ZZ'),
    )
    # Convert Google IDs to internal ideas (which are the same, but with a gc- prefix)
    for student_json in students:
        google_id = student_json['profile']['id']
        local_id = learning_observer.auth.google_id_to_user_id(google_id)
        student_json['user_id'] = local_id
        del student_json['profile']['id']

        # For the present there is only one external id so we will add that directly.
        if 'external_ids' not in student_json['profile']:
            student_json['profile']['external_ids'] = []
        student_json['profile']['external_ids'].append({"source": "google", "id": google_id})
    return students


@register_cleaner("course_list", "courses")
def clean_course_list(google_json):
    '''
    Google's course list is one object deeper than we'd like, and alphabetic
    sort order is nicer. This will clean it up a bit
    '''
    courses = google_json.get('courses', [])
    courses.sort(
        key=lambda x: x.get('name', 'ZZ'),
    )
    return courses


# Google Docs
def _force_text_length(text, length):
    '''
    Force text to a given length, either concatenating or padding

    >>> force_text_length("Hello", 3)
    >>> 'Hel'

    >>> force_text_length("Hello", 13)
    >>> 'Hello        '
    '''
    return text[:length] + " " * (length - len(text))


@register_cleaner("document", "doctext")
def extract_text_from_google_doc_json(
        j, align=True,
        EXTRACT_DEBUG_CHECKS=False):
    '''
    Extract text from a Google Docs JSON object, ignoring formatting.

    There is an alignment issue between Google's and Python's handling
    of Unicode. We can either:
    * extract text faithfully (align=False)
    * extract text with aligned indexes by cutting text / adding
      spaces (align=True)

    This issue came up in text with a Russian flag unicode symbol
    (referencing the current conflict). I tried various encodings,
    and none quite matched Google 100%.

    Note that align=True doesn't necessarily give perfect local alignment
    within text chunks, since we do have different lengths for something like
    this flag. It does work okay globally.
    '''
    # return error message for text
    if 'error' in j:
        return f"Error {j['error']['code']} {j['error']['status']}\n{j['error']['message']}"
    length = j['body']['content'][-1]['endIndex']
    elements = [a.get('paragraph', {}).get('elements', []) for a in j['body']['content']]
    flat = sum(elements, [])
    text_chunks = [f['textRun']['content'] for f in flat]
    if align:
        lengths = [f['endIndex'] - f['startIndex'] for f in flat]
        text_chunks = [_force_text_length(chunk, length) for chunk, length in zip(text_chunks, lengths)]
    text = ''.join(text_chunks)

    if EXTRACT_DEBUG_CHECKS:
        print("Text length versus Google length:")
        print(len(text), length)
        print("We expect these to be off by one, since Google seems to starts at 1 (and Python at 0)")
        if align:
            print
            print("Offsets (these should match):")
            print(list(zip(itertools.accumulate(map(len, text_chunks)), itertools.accumulate(lengths))))

    return text


if __name__ == '__main__':
    import json
    import sys
    j = json.load(open(sys.argv[1]))
    extract_text_from_google_doc_json(j, align=False, EXTRACT_DEBUG_CHECKS=True)
    extract_text_from_google_doc_json(j, align=True, EXTRACT_DEBUG_CHECKS=True)
