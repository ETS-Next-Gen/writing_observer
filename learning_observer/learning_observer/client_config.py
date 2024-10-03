'''
Client Configuration
====================

This module creates a client-side configuration. This might include
things such as:

- Relative URL paths
- Per-server UX tweaks
- Etc.
'''

import aiohttp
import pmss

import learning_observer.settings
import learning_observer.auth.http_basic

# TODO where should we define the theme items?
pmss.register_field(
    name='server_name',
    type=pmss.pmsstypes.TYPES.string,
    description='Name of the server to include on the login page.',
    default='Learning Observer'
)
pmss.register_field(
    name='front_page_pitch',
    type=pmss.pmsstypes.TYPES.string,
    description='Short server description to include on the login page.'
)
pmss.register_field(
    name='logo_big',
    type=pmss.pmsstypes.TYPES.string,
    description='Path to logo to display on the login page.'
)
# This item is used in routes, but we are leaving it here
# along with the rest of the `theme` items.
pmss.register_field(
    name='root_file',
    type=pmss.pmsstypes.TYPES.string,
    description="We'd like to be able to have the root page themeable, for non-ETS deployments. This is a quick-and-dirty way to override the main page.",
    default='webapp.html'
)


async def client_config_handler(request):
    '''
    Return a configuration JSON response to the client. This:
    - Tells the client this is running from a live server
    - Includes any system-specific configuration

    For debugging / devel, it's helpful to be able to mock the API
    with static files. Those won't do things like web sockets. In that
    case, we can host this client-side configuration on a local
    server as a static file, with `mode` set to `static`.
    '''
    client_config = {
        "mode": "server",
        "modules": {  # Per-module config
            'wobserver': {
                'hide_labels': False  # TODO: Should be loaded from config file
            }
        },
        "google_oauth": learning_observer.settings.pmss_settings.google_oauth_enabled(types=['auth']),
        "password_auth": learning_observer.settings.pmss_settings.password_file_enabled(types=['auth']),
        "http_basic_auth": learning_observer.auth.http_basic.http_auth_page_enabled(),
        "theme": {
            'server_name': learning_observer.settings.pmss_settings.server_name(types=['theme']),
            'front_page_pitch': learning_observer.settings.pmss_settings.front_page_pitch(types=['theme']),
            'logo_big': learning_observer.settings.pmss_settings.logo_big(types=['theme']),
        }
    }

    return aiohttp.web.json_response(client_config)
