'''
We will gradually move all of the Google-specific code into here.

Our design goals:
- Easily call into Google APIs (Classroom, Drive, Docs, etc.)
- Be able to preprocess the data into standard formats
'''

import itertools

import aiohttp
import aiohttp.web

import learning_observer.settings as settings

# These took a while to find, but many are documented here:
# https://developers.google.com/drive/api/v3/reference/
# This list might change. Many of these contain additional (optional) parameters
# which we might add later. This is here for debugging, mostly. We'll stabilize
# APIs later.
#
# This should probably not be a list, eventually.
DEFAULT_URLS = [
    ("document", "/google/docs/{documentId}", "https://docs.googleapis.com/v1/documents/{documentId}"),
    ("course_list", "/google/courses", "https://classroom.googleapis.com/v1/courses"),
    ("course_roster", "/google/roster/{courseId}", "https://classroom.googleapis.com/v1/courses/{courseId}/students"),
    ("drive_files", "/google/listfiles", "https://www.googleapis.com/drive/v3/files"),    # This paginates. We only return page 1.
    ("drive_about", "/google/drive/about", "https://www.googleapis.com/drive/v3/about?fields=%2A"),  # Fields=* probably gives us more than we need
    ("drive_comments", "/google/drive/comments/{documentId}", "https://www.googleapis.com/drive/v3/files/{documentId}/comments?fields=%2A&includeDeleted=true"),
    ("drive_revisions", "/google/drive/revisions/{documentId}", "https://www.googleapis.com/drive/v3/files/{documentId}/revisions")
]

async def raw_google_ajax(request, target_url, **kwargs):
    '''
    Make an AJAX call to Google, managing auth + auth.

    * request is the aiohttp request object.
    * default_url is typically grabbed from DEFAULT_URLs
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

        print(await raw_document(request, documentId="1t27dWsD_IOeByc5aBL9b0Pmf2VEVLrKuOswVdMUXN9w"))
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to Google
        '''
        return await raw_google_ajax(request, remote_url, **kwargs)
    setattr(caller, "__qualname__", name)

    return caller

# We create function calls for each of the Google APIs. For example:
#   raw_document()
#   raw_course_list()
# etc.
for name, local_url, remote_url in DEFAULT_URLS:
    function_name = f"raw_{name}"
    globals()[function_name] = raw_access_partial(remote_url=remote_url, name=name)


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

    if not isinstance(settings.settings['feature_flags'], dict) or \
        'urls' not in settings.settings['feature_flags']:
        urls = DEFAULT_URLS
    else:
        urls = settings.settings['feature_flags']['urls']

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

    for (name, url, remote_url) in urls:
        app.add_routes([
            aiohttp.web.get(
                url,
                handler(remote_url)
            )
        ])


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


if __name__=='__main__':
    import json, sys
    j = json.load(open(sys.argv[1]))
    extract_text_from_google_doc_json(j, align=False, EXTRACT_DEBUG_CHECKS=True)
    extract_text_from_google_doc_json(j, align=True, EXTRACT_DEBUG_CHECKS=True)
    
