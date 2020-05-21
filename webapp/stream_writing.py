'''Stream fake writing data

Usage:
    stream_writing.py [--url=<url>] [--user=<user_id>] [--ici=<secs>]
                      [--source=<filename>] [--text-length=5]
                      [--doc_id=<google_doc_id>]

Options
    --url=<url>            URL to connect [default: http://localhost:8888/]
    --user=<user_id>       Supply the user ID [default: 1]
    --ici=<seconds>        Mean intercharacter interval [default: 0.1]
    --source=<filename>    Stream text instead of lorem ipsum
    --text-length=<n>      Number of paragraphs of lorem ipsum [default: 5]
    --doc_id=<google_doc>  Google document ID to spoof [default: testabcd1234]

Overview:

    Stream fake keystroke data to a server, emulating Google Docs
    logging. Currently, this streams one document. It can be trivially
    modified to stream multiple, once the server is ready.
'''

import asyncio
import json
import sys

import aiohttp
import docopt

import loremipsum

ARGS = docopt.docopt(__doc__)
print(ARGS)

if ARGS['--source'] is None:
    TEXT = "\n".join(loremipsum.get_paragraphs(5))
else:
    TEXT = open(ARGS['--source']).read()

print(TEXT)


def insert(index, text):
    '''
    Generate a minimal 'insert' event, of the type our Google Docs extension
    might send, but with irrelevant stuff stripped away. This is just for
    testing.
    '''
    return {
        "bundles": [{'commands': [{"ibi": index, "s": text, "ty": "is"}]}],
        "event": "google_docs_save",
        "source": "org.mitros.writing-analytics",
        "doc_id": ARGS["--doc_id"],
        "origin": "stream-test-script"
    }


async def stream_document(text):  #  to do:  user=None
    '''
    Send a document to the server. To do: Figure out how to handle
    users.
    '''
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ARGS["--url"]) as web_socket:
            for char, index in zip(text, range(len(text))):
                command = insert(index+1, char)
                await web_socket.send_str(json.dumps(command))
                await asyncio.sleep(float(ARGS["--ici"]))


async def run():
    '''
    Create a task to send the document to the server, and wait
    on it to finish. In the future, we'll create several tasks.
    '''
    streamer = asyncio.create_task(stream_document(TEXT))
    await streamer

try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)
