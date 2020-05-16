'''
ReStream

Usage:
    restream.py [--url=<url>] <filename>

Options
    --url=<url>   URL to connect [default: http://localhost:8888/]

Overview:
    * Restream logs from a file a web sockets server
    * Helpful for testing
    * Optional (todo): Capture server output
    * Optional (todo): Handle AJAX
'''

import asyncio
import sys

import aiofiles
import aiohttp
import docopt


async def run():
    '''
    Simplest function in the world.

    Open up a session, then a socket, and then stream lines from the
    file to the socket.

    Is there a way to clean up so we don't have an ever-expanding
    block indent?
    '''
    args = docopt.docopt(__doc__)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(args["--url"]) as web_socket:
            async with aiofiles.open(args['<filename>']) as log_file:
                async for line in log_file:
                    await web_socket.send_str(line.strip())

try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)
