'''
Stream fake writing data

Usage:
    stream_writing.py [--url=url] [--streams=n]
                      [--ici=sec,s,s,...]
                      [--users=user_id,uid,uid,...]
                      [--source=filename,fn,fn,...]
                      [--gdids=googledoc_id,gdi,gdi,...]
                      [--text-length=5]

Options:
    --url=url                URL to connect [default: http://localhost:8888/]
    --streams=N              How many students typing in parallel? [default: 1]
    --users=user_id,uid,uid  Supply the user ID
    --ici=secs,secs          Mean intercharacter interval [default: 0.1]
    --gdids=gdi,gdi,gdi      Google document IDs of spoofed documents
    --source=filename        Stream text instead of lorem ipsum
    --text-length=n          Number of paragraphs of lorem ipsum [default: 5]

Overview:
    Stream fake keystroke data to a server, emulating Google Docs
    logging.

    Note that this has only been tested with one stream. We need
    server support to test with more.
'''

import asyncio
import json
import sys

import aiohttp
import docopt

import loremipsum

ARGS = docopt.docopt(__doc__)
print(ARGS)

STREAMS = int(ARGS["--streams"])

if ARGS['--source'] == []:
    TEXT = ["\n".join(loremipsum.get_paragraphs(5))] * STREAMS
else:
    filenames = ARGS['--source']
    if len(filenames) == 1:
        filenames = filenames * STREAMS
    TEXT = [open(filename).read() for filename in filenames]

if len(ARGS['--ici']) == 1:
    ICI = ARGS['--ici'] * STREAMS
else:
    ICI = ARGS['--ici']

if ARGS['--users'] == []:
    USERS = ["test-user-{n}".format(n=i) for i in range(STREAMS)]
else:
    USERS = ARGS['--users']

if ARGS["--gdids"] == []:
    DOC_IDS = ["fake-google-doc-id-{n}".format(n=i) for i in range(STREAMS)]
else:
    DOC_IDS = ARGS["--gdids"]

assert len(TEXT) == STREAMS, "len(filenames) != STREAMS."
assert len(ICI) == STREAMS, "len(ICIs) != STREAMS."
assert len(USERS) == STREAMS, "len(users) != STREAMS."
assert len(DOC_IDS) == STREAMS, "len(document IDs) != STREAMS."


def insert(index, text, doc_id):
    '''
    Generate a minimal 'insert' event, of the type our Google Docs extension
    might send, but with irrelevant stuff stripped away. This is just for
    testing.
    '''
    return {
        "bundles": [{'commands': [{"ibi": index, "s": text, "ty": "is"}]}],
        "event": "google_docs_save",
        "source": "org.mitros.writing-analytics",
        "doc_id": doc_id,
        "origin": "stream-test-script"
    }


def identify(user):
    '''
    Send a token identifying user.

    TBD: How we want to manage this. We're still figuring out auth/auth.
    This might just be scaffolding code for now, or we might do something
    along these lines.
    '''
    return [
        {
            "event": "test_framework_fake_identity",
            "source": "org.mitros.writing-analytics",
            "user_id": user,
            "origin": "stream-test-script"
        }, {
            "event": "metadata_finished",
            "source": "org.mitros.writing-analytics",
            "origin": "stream-test-script"
        }
    ]


async def stream_document(text, ici, user, doc_id):
    '''
    Send a document to the server.
    '''
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ARGS["--url"]) as web_socket:
            commands = identify(user)
            for command in commands:
                await web_socket.send_str(json.dumps(command))
            for char, index in zip(text, range(len(text))):
                command = insert(index + 1, char, doc_id)
                await web_socket.send_str(json.dumps(command))
                await asyncio.sleep(float(ici))


async def run():
    '''
    Create a task to send the document to the server, and wait
    on it to finish. In the future, we'll create several tasks.
    '''
    streamers = [
        asyncio.create_task(stream_document(text, ici, user, doc_id))
        for (text, ici, user, doc_id) in zip(TEXT, ICI, USERS, DOC_IDS)
    ]
    print(streamers)
    for streamer in streamers:
        await streamer
    print(streamers)

try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)
