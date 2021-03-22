'''
Minimal test server. Serves up a git repo passed on the command line.

Usage:

>>> python test_server /home/ubuntu/repo/
'''

import sys

import asyncio
import aiohttp.web

import aio_gitserve


gitrepo = sys.argv[1]

loop = asyncio.get_event_loop()
app = aiohttp.web.Application(loop=loop)
app.router.add_get(
    '/',
    lambda request: aiohttp.web.Response(text='Test / example server!')
)
app.router.add_get(
    r'/browse/{branch:[^{}/]+}/{filename:[^{}]+}',
    aio_gitserve.git_handler_wrapper(gitrepo)
)
aiohttp.web.run_app(app, host='127.0.0.1', port=8080)
