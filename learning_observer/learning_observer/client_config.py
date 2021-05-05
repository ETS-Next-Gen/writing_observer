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

import learning_observer.settings


client_config = {
    # Tell the client there's a live server
    #
    # For debugging / devel, it's helpful to be able to mock the API
    # with static files. Those won't do things like web sockets.
    "mode": "server",
    "modules": {},     # Per-module config
    "google-oauth": "google-oauth" in learning_observer.settings.settings['auth'],
    "password-auth": "password-file" in learning_observer.settings.settings['auth'],
    "theme": learning_observer.settings.settings['theme']
}


async def client_config_handler(request):
    '''
    Return a configuration JSON response to the client. This:
    - Tells the client this is running from a live server
    - Includes any system-specific configuration
    '''
    return aiohttp.web.json_response(client_config)
