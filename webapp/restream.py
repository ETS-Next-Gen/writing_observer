'''
ReStream

Usage:
    restream.py [--url=<url>] [--extract-client] [--rate=<rate>] [--max-wait=<sec>] <filename>

Options
    --url=<url>       URL to connect [default: http://localhost:8888/]
    --extract-client  Parse JSON and extract client-side event
    --rate=<rate>     Throttle events to: rate*timestamps
    --max-wait=<sec>  Maximum delay (if throttling)

Overview:
    * Restream logs from a file a web sockets server
    * Helpful for testing
    * Optional (todo): Capture server output
    * Optional (todo): Handle AJAX
'''

import asyncio
import json
import sys

import aiofiles
import aiohttp
import docopt

print(docopt.docopt(__doc__))


async def run():
    '''
    Simplest function in the world.

    Open up a session, then a socket, and then stream lines from the
    file to the socket.

    Is there a way to clean up so we don't have an ever-expanding
    block indent?
    '''
    args = docopt.docopt(__doc__)
    print(args['--extract-client'])
    old_ts = None

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(args["--url"]) as web_socket:
            async with aiofiles.open(args['<filename>']) as log_file:
                async for line in log_file:
                    if args["--rate"] is not None:
                        new_ts = json.loads(line)["server"]["time"]
                        if old_ts is not None:
                            rate = float(args["--rate"])
                            delay = (new_ts-old_ts)*rate
                            if args["--max-wait"] is not None:
                                delay = min(delay, float(args["--max-wait"]))
                            print(line)
                            print(delay)
                            await asyncio.sleep(delay)
                        old_ts = new_ts
                    if args['--extract-client']:
                        line = json.dumps(json.loads(line)['client'])
                    await web_socket.send_str(line.strip())
try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)
