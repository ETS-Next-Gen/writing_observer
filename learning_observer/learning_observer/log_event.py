# For now, we dump logs into files, crudely.
#
# We're not there yet, but we would like to create a 哈希树, or
# Merkle-tree-style structure for our log files.
#
# Or to be specific, a Merkle DAG, like git.
#
# Each item is stored under its SHA hash. Note that items are not
# guaranteed to exist. We can prune them, and leave a dangling pointer
# with just the SHA.
#
# Each event log will be structured as
#    +-----------------+     +-----------------+
# <--- Last item (SHA) |  <--- Last item (SHA) | ...
#    |                 |     |                 |
#    |   Data (SHA)    |     |    Data (SHA)   |
#    +-------|---------+     +--------|--------+
#            |                        |
#            v                        v
#        +-------+                +-------+
#        | Event |                | Event |
#        +-------+                +-------+
#
# Where the top objects form a linked list (each containing a pair of
# SHA hashes, one of the previous item, and one of the associated
# event).
#
# We will then have a hierarchy, where we have lists per-document,
# documents per-student. When we run analyses, those will store the
# hashes of where in each event log we are. Likewise, with each layer
# of analysis, we'll store pointers to git hashes of code, as well as
# of intermediate files (and how those were generated).
#
# Where data is available, we can confirm we're correctly replicating
# prior tesults.
#
# The planned data structure is very similar to git, but with the
# potential for missing data without an implosion.
#
# Where data might not be available is after a FERPA, CCPA, or GDPR
# requests to change data. In those cases, we'll have dangling nodes,
# where we'll know that data used to exist, but not what it was.
#
# We might also have missing intermediate files. For example, if we do
# a dozen analyses, we'll want to know those happened and what those
# were, but we might not keep terabytes of data around (just enough to
# redo those analyses).

import datetime
import inspect
import json
import hashlib

import filesystem_state

import paths


mainlog = open(paths.logs("main_log.json"), "ab", 0)
files = {}


def encode_json_line(line):
    '''
    For encoding short data, such as an event.

    We use a helper function so we have the same encoding
    everywhere. Our primary goal is replicability -- if
    we encode the same dictionary twice, we'd like to get
    the same string, with the same hash.
    '''
    return json.dumps(line, sort_keys=True)


def encode_json_block(block):
    '''
    For encoding large data, such as the startup log.

    We use a helper function so we have the same encoding
    everywhere. Our primary goal is replicability -- if
    we encode the same dictionary twice, we'd like to get
    the same string, with the same hash.
    '''
    return json.dumps(block, sort_keys=True, indent=3)


def secure_hash(text):
    '''
    Our standard hash functions. We can either use either

    * A full hash (e.g. SHA3 512) which should be secure against
    intentional attacks (e.g. a well-resourced entity wants to temper
    with our data, or if Moore's Law starts up again, a well-resourced
    teenager).

    * A short hash (e.g. MD5), which is no longer considered
    cryptographically-secure, but is good enough to deter casual
    tempering. Most "tempering" comes from bugs, rather than attackers,
    so this is very helpful still. MD5 hashes are a bit more manageable
    in size.

    For now, we're using full hashes everywhere, but it would probably
    make sense to alternate as makes sense. MD5 is 32 characters, while
    SHA3_512 is 128 characters (104 if we B32 encode).
    '''
    return "SHA512_" + hashlib.sha3_512(text).hexdigest()


def insecure_hash(text):
    '''
    See `secure_hash` above for documentation
    '''
    return "MD5_" + hashlib.md5(text).hexdigest()


# We're going to save the state of the filesystem on application startup
# This way, event logs can refer uniquely to running version
# Do we want the full 512 bit hash? Cut it back? Use a more efficient encoding than
# hexdigest?
startup_state = json.dumps(filesystem_state.filesystem_state(), indent=3, sort_keys=True)
STARTUP_STATE_HASH = secure_hash(startup_state.encode('utf-8'))
STARTUP_FILENAME = "{directory}/{time}-{hash}.json".format(
    directory=paths.logs("startup"),
    time=datetime.datetime.utcnow().isoformat(),
    hash=STARTUP_STATE_HASH
)

with open(STARTUP_FILENAME, "w") as fp:
    # gzip can save about 2-3x space. It makes more sense to do this
    # with larger files later. tar.gz should save a lot more
    fp.write(startup_state)


def log_event(event, filename=None, preencoded=False, timestamp=False):
    if filename is None:
        fp = mainlog
    elif filename in files:
        return files[filename]
    else:
        fp = open(paths.logs("" + filename + ".log"), "ab", 0)
        files[filename] = fp

    if not preencoded:
        event = json.dumps(event, sort_keys=True)
    fp.write(event.encode('utf-8'))
    if timestamp:
        fp.write("\t".encode('utf-8'))
        fp.write(datetime.datetime.utcnow().isoformat().encode('utf-8'))
    fp.write("\n".encode('utf-8'))
    fp.flush()


def debug_log(text):
    '''
    Helper function to help us trace our code.

    We print a time stamp, a stack trace, and a /short/ summary of
    what's going on.

    This is not intended for programmatic debugging. We do change
    format regularly (and you should feel free to do so too -- for
    example, on narrower terminals, a `\n\t` can help)
    '''
    stack = inspect.stack()
    stack_trace = "{s1}/{s2}/{s3}".format(
        s1=stack[1].function,
        s2=stack[2].function,
        s3=stack[3].function,
    )

    message = "{time}: {st:60}\t{body}".format(
        time=datetime.datetime.utcnow().isoformat(),
        st=stack_trace,
        body=text
    )

    # Flip here to print / not print debug messages
    if True:
        print(message)

    # Flip here to save / not save debug messages
    # Ideally, we'd like to log these somewhere which won't cause cascading failures.
    # If we e.g. have errors every 100ms, we don't want to create millions of debug files.
    # There are services which handle this pretty well, I believe
    if True:
        fp = open(paths.logs("debug.log"), "a")
        fp.write(message)
        fp.write("\n")
        fp.close()


def log_ajax(url, resp_json, request):
    '''
    This is primarily used to log the responses of AJAX requests made
    TO Google and similar providers. This helps us understand the
    context of classroom activity, debug, and recover from failures
    '''
    AJAX_FILENAME_TEMPLATE = "{directory}/{time}-{payload_hash}.json"
    payload = {
        'user': request['user'],
        'url': url,
        'response': resp_json,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    encoded_payload = encode_json_block(payload)
    payload_hash = secure_hash(encoded_payload.encode('utf-8'))
    filename = AJAX_FILENAME_TEMPLATE.format(
        directory=paths.logs("ajax"),
        time=datetime.datetime.utcnow().isoformat(),
        payload_hash=payload_hash
    )
    with open(filename, "w") as fp:
        fp.write(encoded_payload)
