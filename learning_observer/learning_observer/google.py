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

import aiohttp
import aiohttp.web

import learning_observer.settings as settings

# These took a while to find, but many are documented here:
# https://developers.google.com/drive/api/v3/reference/
# This list might change. Many of these contain additional (optional) parameters
# which we might add later. This is here for debugging, mostly. We'll stabilize
# APIs later.
Endpoint = collections.namedtuple("Endpoint", ["name", "local_url", "remote_url", "doc", "cleaners"], defaults=[[], ""])

ENDPOINTS = list(map(lambda x: Endpoint(*x), [
    ("document", "/google/docs/{documentId}", "https://docs.googleapis.com/v1/documents/{documentId}"),
    ("course_list", "/google/courses", "https://classroom.googleapis.com/v1/courses"),
    ("course_roster", "/google/courses/{courseId}/students", "https://classroom.googleapis.com/v1/courses/{courseId}/students"),
    ("course_work", "/google/courses/{courseId}/coursework", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork"),
    ("submissions", "/google/courses/{courseId}/submissions/{courseWorkId}", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork/{courseWorkId}/studentSubmissions"),
    ("materials", "/google/courses/{courseId}/materials", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWorkMaterials"),
    ("topics", "/google/courses/{courseId}/topics", "https://classroom.googleapis.com/v1/courses/{courseId}/topics"),
    ("drive_files", "/google/drive/files", "https://www.googleapis.com/drive/v3/files"),    # This paginates. We only return page 1.
    ("drive_about", "/google/drive/about", "https://www.googleapis.com/drive/v3/about?fields=%2A"),  # Fields=* probably gives us more than we need
    ("drive_comments", "/google/drive/{documentId}/comments", "https://www.googleapis.com/drive/v3/files/{documentId}/comments?fields=%2A&includeDeleted=true"),
    ("drive_revisions", "/google/drive/{documentId}/revisions", "https://www.googleapis.com/drive/v3/files/{documentId}/revisions")
]))

async def raw_google_ajax(request, target_url, **kwargs):
    '''
    Make an AJAX call to Google, managing auth + auth.

    * request is the aiohttp request object.
    * default_url is typically grabbed from ENDPOINTS
    * ... and we pass the named parameters
    '''
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        url = target_url.format(**kwargs)
        async with client.get(url, headers=request["auth_headers"]) as resp:
            return await resp.json()


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


def register_module_function_calls():
    '''
    We create function calls for each of the Google APIs. For example:
       raw_document()
       raw_course_list()
    etc.

    This called on import, at the very end.
    '''
    # Raw function calls
    for e in ENDPOINTS:
        function_name = f"raw_{e.name}"
        globals()[function_name] = raw_access_partial(remote_url=e.remote_url, name=e.name)


def register_google_debug_routes(app):
    '''
    Apps to pass through AJAX requests to Google

    This is for debugging, primarily. We'll figure out if we want production
    APIs from this later.

    This is more useful than it looks, since making use of Google APIs requires
    a lot of infrastructure (registering apps, auth/auth, etc.) which we already
    have in place on dev / debug servers.

    A lot of this code should move out of here into a dedicated Google API
    module, with just the piece to set up routes left here.
    '''
    if 'google_routes' not in settings.settings['feature_flags']:
        return

    app.add_routes([
        aiohttp.web.get("/google/doctext/{documentId}", google_docs_text_handler)
    ])

    def handler(remote_url):
        '''
        This creates a handler to forward Google requests to the client. It's used
        for debugging right now. We should think through APIs before relying on this.
        '''
        async def ajax_passthrough(request):
            '''
            And the actual handler....
            '''
            return aiohttp.web.json_response(await raw_google_ajax(
                request,
                remote_url,
                **request.match_info
            ))
        return ajax_passthrough

    for e in ENDPOINTS:
        app.add_routes([
            aiohttp.web.get(
                e.local_url,
                handler(e.remote_url)
            )
        ])


async def google_docs_text_handler(request):
    '''
    Return a Google Doc as plain text.
    '''
    return aiohttp.web.Response(
        text=extract_text_from_google_doc_json(
            await raw_document(request, **request.match_info)
        )
    )



async def course_roster_handler(request):
    pass


async def course_roster(request):
    pass


# Rosters
async def clean_course_roster(google_json):
    pass


async def clean_course_list(google_json):
    '''
    Google's course list is one object deeper than we'd like, and alphabetic
    sort order is nicer. This will clean it up a bit
    '''
    courses = google_json['courses']
    courses.sort(
        sort_key=lambda x: x.get('name', 'ZZ'),
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
    return text[:length] + " " * (length-len(text))


def extract_text_from_google_doc_json(
        j, align=True,
        EXTRACT_DEBUG_CHECKS = False):
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
    length = j['body']['content'][-1]['endIndex']
    elements = [a.get('paragraph', {}).get('elements', []) for a in j['body']['content']]
    flat = sum(elements, [])
    text_chunks = [f['textRun']['content'] for f in flat]
    if align:
        lengths = [f['endIndex']-f['startIndex'] for f in flat]
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

register_module_function_calls()

if __name__=='__main__':
    import json, sys
    j = json.load(open(sys.argv[1]))
    extract_text_from_google_doc_json(j, align=False, EXTRACT_DEBUG_CHECKS=True)
    extract_text_from_google_doc_json(j, align=True, EXTRACT_DEBUG_CHECKS=True)
