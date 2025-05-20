'''
Generic API calling infrastructure that can be reused for different APIs.

Design goals:
- Easily call into external APIs
- Be able to preprocess the data into standard formats

On a high level, for each API request, we plan to have a 4x4 grid:
- Web request and function call
- Cleaned versus raw data

For each specific API implementation, we'll have both raw data access and cleaner functions
to transform that data into more convenient formats.
'''
import inspect
import json
import recordclass
import string

import aiohttp
import aiohttp.web

import learning_observer.constants as constants
import learning_observer.settings as settings
import learning_observer.log_event
import learning_observer.auth
import learning_observer.runtime


class Endpoint(recordclass.make_dataclass("Endpoint", ["name", "remote_url", "doc", "cleaners", "api_name"], defaults=["", None, None])):
    def arguments(self):
        return extract_parameters_from_format_string(self.remote_url)

    def _local_url(self):
        parameters = "}/{".join(self.arguments())
        base_url = f"/{self.api_name}/{self.name}"
        if len(parameters) == 0:
            return base_url
        else:
            return base_url + "/{" + parameters + "}"

    def _add_cleaner(self, name, cleaner):
        if self.cleaners is None:
            self.cleaners = dict()
        self.cleaners[name] = cleaner
        if 'local_url' not in cleaner:
            cleaner['local_url'] = self._local_url() + "/" + name

    def _cleaners(self):
        if self.cleaners is None:
            return []
        else:
            return self.cleaners


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


async def raw_api_ajax(runtime, target_url, key_translator=None, cache=None, cache_key_prefix=None, **kwargs):
    '''
    Make an AJAX call to an API, managing auth + auth.

    * runtime is a Runtime class containing request information.
    * target_url is typically grabbed from ENDPOINTS
    * key_translator is a dictionary to translate API keys to internal keys
    * cache is an optional cache object
    * cache_key_prefix is the prefix to use for cache keys
    * ... and we pass the named parameters
    '''
    request = runtime.get_request()
    url = target_url.format(**kwargs)
    user = await learning_observer.auth.get_active_user(request)

    if constants.AUTH_HEADERS not in request or user is None:
        raise aiohttp.web.HTTPUnauthorized(text="Please log in")

    auth_headers = request[constants.AUTH_HEADERS]
    cache_available = cache is not None and cache_key_prefix is not None

    if cache_available:
        cache_key = f"{cache_key_prefix}/{learning_observer.auth.encode_id('session', user[constants.USER_ID])}/{learning_observer.util.url_pathname(url)}"
        if settings.feature_flag('save_clean_ajax') is not None:
            value = await cache[cache_key]
            if value is not None:
                response_data = json.loads(value)
                if key_translator:
                    return learning_observer.util.translate_json_keys(response_data, key_translator)
                return response_data

    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        async with client.get(url, headers=auth_headers) as resp:
            response = await resp.json()
            learning_observer.log_event.log_ajax(target_url, response, request)

            if cache_available:
                if settings.feature_flag('use_clean_ajax') is not None:
                    await cache.set(cache_key, json.dumps(response, indent=2))

            if key_translator:
                return learning_observer.util.translate_json_keys(response, key_translator)
            return response


def raw_access_partial(remote_url, key_translator=None, cache=None, cache_key_prefix=None, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    API endpoints.
    '''
    async def caller(runtime, **kwargs):
        '''
        Make an AJAX request to the API
        '''
        return await raw_api_ajax(
            runtime, 
            remote_url, 
            key_translator, 
            cache, 
            cache_key_prefix,
            **kwargs
        )

    if name:
        setattr(caller, "__qualname__", name)

    return caller


def register_endpoints(app, endpoints, api_name, key_translator=None, cache=None, cache_key_prefix=None, feature_flag_name=None):
    '''
    Initialize API routes and handlers:

    - Creates debug routes to pass through AJAX requests to API
    - Creates production APIs to have access to cleaned versions of data
    - Creates local function calls to call from other pieces of code within process

    Parameters:
    - app: The aiohttp application to which routes will be added
    - endpoints: List of Endpoint objects describing API endpoints
    - api_name: Name of the API (e.g., "google", "canvas")
    - key_translator: Dictionary to translate API keys to internal keys
    - cache: Cache object for API responses
    - cache_key_prefix: Prefix for cache keys
    - feature_flag_name: Feature flag to check before enabling routes
    '''
    # Check feature flag if provided
    if feature_flag_name and not settings.feature_flag(feature_flag_name):
        return

    # Provide documentation on what we're doing
    async def api_docs_handler(request):
        '''Return a list of available endpoints.'''
        response = f"{api_name.capitalize()} API Endpoints:\n"
        for endpoint in endpoints:
            response += f"{endpoint._local_url()}\n"
            cleaners = endpoint._cleaners()
            for c in cleaners:
                response += f"   {cleaners[c]['local_url']}\n"
        return aiohttp.web.Response(text=response)

    app.add_routes([
        aiohttp.web.get(f"/{api_name}", api_docs_handler)
    ])

    def make_ajax_raw_handler(remote_url):
        '''
        Creates a handler to forward API requests to the client.
        '''
        async def ajax_passthrough(request):
            '''The actual handler.'''
            runtime = learning_observer.runtime.Runtime(request)
            response = await raw_api_ajax(
                runtime,
                remote_url,
                key_translator,
                cache,
                cache_key_prefix,
                **request.match_info
            )
            return aiohttp.web.json_response(response)
        return ajax_passthrough

    def make_cleaner_handler(raw_function, cleaner_function, name=None):
        async def cleaner_handler(request):
            # TODO check if we need the runtime here
            runtime = learning_observer.runtime.Runtime(request)
            response = cleaner_function(
                await raw_function(runtime, **request.match_info)
            )
            if inspect.isawaitable(response):
                response = await response
            if isinstance(response, dict) or isinstance(response, list):
                return aiohttp.web.json_response(response)
            elif isinstance(response, str):
                return aiohttp.web.Response(text=response)
            else:
                raise AttributeError(f"Invalid response type: {type(response)}")

        if name is not None:
            setattr(cleaner_handler, "__qualname__", name + "_handler")
        return cleaner_handler

    def make_cleaner_function(raw_function, cleaner_function, name=None):
        async def cleaner_local(runtime, **kwargs):
            api_response = await raw_function(runtime, **kwargs)
            clean = cleaner_function(api_response)
            if inspect.isawaitable(clean):
                clean = await clean
            return clean
        if name is not None:
            setattr(cleaner_local, "__qualname__", name)
        return cleaner_local

    # Setup the global namespace using the provided namespace dict
    result_functions = {}

    for e in endpoints:
        function_name = f"raw_{e.name}"
        raw_function = raw_access_partial(
            remote_url=e.remote_url, 
            key_translator=key_translator,
            cache=cache,
            cache_key_prefix=cache_key_prefix,
            name=e.name
        )
        result_functions[function_name] = raw_function
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
            result_functions[cleaners[c]['name']] = make_cleaner_function(
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

    return result_functions


def make_cleaner_registrar(endpoints):
    '''
    Creates a register_cleaner function specific to a list of endpoints.

    Returns:
        A function that can be used as a decorator to register cleaners.
    '''
    def register_cleaner(data_source, cleaner_name):
        '''
        Registers a cleaner function for export both as a web service
        and as a local function call.
        '''
        def decorator(f):
            found = False
            for endpoint in endpoints:
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

    return register_cleaner
