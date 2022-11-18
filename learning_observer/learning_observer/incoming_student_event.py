'''
This has event handlers for incoming student events.

These should come in over a websocket. We support AJAX too, since it's
nice for debugging. This should never be used in production.

We:
* Authenticate (minimally, for now, see docs)
* Run these through a set of reducers
'''

import asyncio
import datetime
import inspect
import json
import os
import time
import traceback
import urllib.parse
import uuid
import socket

import aiohttp

import learning_observer.log_event as log_event
import learning_observer.paths as paths

import learning_observer.auth.utils as authutils               # Encoded / decode user IDs
import learning_observer.stream_analytics as stream_analytics  # Individual analytics modules

import learning_observer.settings as settings

import learning_observer.stream_analytics.helpers

from learning_observer.log_event import debug_log

import learning_observer.exceptions

import learning_observer.auth.events
import learning_observer.adapters.adapter


def compile_server_data(request):
    '''
    We extract some basic data. In contrast to client data, this data
    cannot be spoofed, and can be super-useful for debugging, as well
    as attack mitigation.
    '''
    return {
        'time': time.time(),
        'origin': request.headers.get('Origin', ''),
        'agent': request.headers.get('User-Agent', ''),
        'ip': request.headers.get('X-Real-IP', ''),
        'executable': 'aio_webapp'
    }


async def student_event_pipeline(metadata):
    '''
    Create an event pipeline, based on header metadata
    '''
    client_source = metadata["source"]
    debug_log("client_source", client_source)
    debug_log("Module", stream_analytics.reducer_modules(client_source))
    analytics_modules = stream_analytics.reducer_modules(client_source)

    # Create an event processor for this user
    # TODO:
    # * Thing like this (esp. below) should happen in parallel:
    #   https://stackoverflow.com/questions/57263090/async-list-comprehensions-in-python
    # * We should create cached modules for each key, rather than this partial evaluation
    #   kludge
    async def prepare_reducer(analytics_module):
        '''
        Prepare a reducer for the analytics module. Note that this is in-place (the
        field is mutated).
        '''
        f = analytics_module['reducer']
        # We're moving to this always being a co-routine. This is
        # backwards-compatibility code which should be remove,
        # eventually. We started with a function, and had an interrim
        # period where both functions and co-routines worked.
        if not inspect.iscoroutinefunction(f):
            debug_log("Not a coroutine", analytics_module)
            raise AttributeError("The reducer {} should be a co-routine".format(analytics_module))

        analytics_module['reducer_partial'] = await analytics_module['reducer'](metadata)
        return analytics_module

    analytics_modules = await asyncio.gather(*[prepare_reducer(am) for am in analytics_modules])

    async def pipeline(parsed_message):
        '''
        And this is the pipeline itself. It takes messages, processes them,
        and, optionally, will inform consumers when there is new data (disabled
        in the current code, since we use polling).
        '''
        if type(parsed_message) is not dict:
            raise ValueError(f"Expected a dict, got {type(parsed_message)}")
        if 'client' not in parsed_message:
            raise ValueError("Expected a dict with a 'client' field")
        if 'event' not in parsed_message['client']:
            raise ValueError("Expected a dict with a 'client' field with an 'event' field")

        debug_log("Processing message {event} from {source}".format(
            event=parsed_message["client"]["event"], source=client_source
        ))

        # Try to run a message through all event processors.
        #
        # To do: Finer-grained exception handling. Right now, if we break, we 
        # don't even run through the remaining processors.
        try:
            processed_analytics = []
            # Go through all the analytics modules
            for am in analytics_modules:
                debug_log("Scope", am['scope'])
                event_fields = {}
                skip = False
                for field in am['scope']:
                    if isinstance(field, learning_observer.stream_analytics.helpers.EventField):
                        debug_log("event", parsed_message)
                        debug_log("field", field)
                        client_event = parsed_message.get('client', {})
                        if field.event not in client_event:
                            debug_log(field.event, "not found")
                            skip = True
                        event_fields[field.event] = client_event.get(field.event)
                if not skip:
                    debug_log("args", event_fields)
                    processed_analytics.append(await am['reducer_partial'](parsed_message, event_fields))
        except Exception as e:
            traceback.print_exc()
            filename = paths.logs("critical-error-{ts}-{rnd}.tb".format(
                ts=datetime.datetime.now().isoformat(),
                rnd=uuid.uuid4().hex
            ))
            fp = open(filename, "w")
            fp.write(json.dumps(parsed_message, sort_keys=True, indent=2))
            fp.write("\nTraceback:\n")
            fp.write(traceback.format_exc())
            fp.close()
            if settings.RUN_MODE == settings.RUN_MODES.DEV:
                raise
        return processed_analytics
    return pipeline

COUNTER = 0

async def handle_incoming_client_event(metadata):
    '''
    Common handler for both Websockets and AJAX events.

    We do a reduce through the event pipeline, and forward on to
    for aggregation on the dashboard side.
    '''
    global COUNTER
    pipeline = await student_event_pipeline(metadata=metadata)

    filename = "{timestamp}-{counter:0>10}-{username}-{pid}.study".format(
        username = metadata.get("auth", {}).get("user_id", "GUEST"),
        timestamp=datetime.datetime.utcnow().isoformat(),
        counter=COUNTER,
        pid=os.getpid()
    )
    COUNTER += 1

    # The adapter allows us to handle old event formats
    adapter = learning_observer.adapters.adapter.EventAdapter()

    async def handler(request, client_event):
        '''
        This is the handler for incoming client events.
        '''
        client_event = adapter.canonicalize_event(client_event)
        debug_log("Compiling event for reducer: " + client_event["event"])
        event = {
            "client": client_event,
            "server": compile_server_data(request),
            "metadata": metadata
        }

        # Log to the main event log file
        log_event.log_event(event)
        # Log the same thing to our study log file. This isn't a good final format, since we
        # mix data with auth, but we want this for now.
        log_event.log_event(
            json.dumps(event, sort_keys=True),
            filename, preencoded=True, timestamp=True)
        await pipeline(event)

    return handler


COUNT = 0


def event_decoder_and_logger(
    request,
    headers=None,
    metadata=None,
    session={}):
    '''
    This is the main event decoder. It is called by the
    websocket handler to log events.

    Parameters:
        request: The request object.
        headers: The header events, which e.g. contain auth
        metadata: Metadata about the request, such as IP. This is
            extracted from the request, which will go away soon.

    Returns:
        A coroutine that decodes and logs events.

    We call this after the header events, with the header events in the
    `headers` parameter. This is because we want to log the header events
    before the body events, so they can be dropped from the Merkle tree
    for privacy. Although in most cases, students can be reidentified
    from the body events, the header events contain explicit identification
    tokens. It is helpful to be able to analyze data with these dropped,
    obfuscated, or otherwise anonymized.

    At present, many body events contain auth as well. We'll want to minimize
    this and tag those events appropriately.

    HACK: We would like clean log files for the first classroom pilot.

    This puts events in per-session files.

    The feature flag has the non-hack implementation.
    '''
    if merkle_config:=settings.feature_flag("merkle"):
        import merkle_store

        storage_class = merkle_store.STORES[merkle_config['store']]
        params=merkle_config.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("Merkle tree params must be a dict (even an empty one)")
        storage = storage_class(**params)
        merkle_store.Merkle(storage)
        session = {
            "student": request.student,
            "tool": request.tool
        }
        merkle_store.start(session)
        def decode_and_log_event(msg):
            '''
            Decode and store the event in the Merkle tree
            '''
            event = json.loads(msg)
            merkle_store.event_to_session(event)
            return event


    global COUNT
    # Count + PID should guarantee uniqueness.
    # With multi-server installations, we might want to add
    # `socket.gethostname()`, but hopefully we'll have our
    # Merkle tree logger by then, and this will be obsolete.
    filename = "{timestamp}-{ip:-<15}-{hip:-<15}-{session_count:0>10}-{pid}".format(
        ip=request.remote,
        hip=request.headers.get('X-Real-IP', ''),
        timestamp=datetime.datetime.utcnow().isoformat(),
        session_count=COUNT,
        pid=os.getpid()
    )
    COUNT += 1

    def decode_and_log_event(msg):
        '''
        Take an aiohttp web sockets message, log it, and return
        a clean event.
        '''
        if isinstance(msg, dict):
            json_event = msg
        else:
            json_event = json.loads(msg.data)
        log_event.log_event(json_event, filename=filename)
        return json_event
    return decode_and_log_event


async def incoming_websocket_handler(request):
    '''
    This handles incoming WebSockets requests. It does some minimal
    processing on them. It used to rely them on via PubSub to be
    aggregated, but we've switched to polling. It also logs them.
    '''
    debug_log("Incoming web socket connected")
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    # For now, we receive two packets to initialize:
    # * Chrome's identity information
    # * browser.storage identity information
    event_metadata = {'headers': {}}

    debug_log("Init pipeline")
    header_events = []

    # This will take a little bit of explaining....
    #
    # We originally did not have a way to do auth/auth. Now, we do
    # auth with a header. However, we have old log files without that
    # header. Setting INIT_PIPELINE to False allows us to use those
    # files in the current system.
    #
    # At some point, we should either:
    #
    # 1) Change restream.py to inject a false header, or archive the
    # source files and migrate the files, so that we can eliminate
    # this setting; or
    # 2) Dispatch on type of event
    #
    # This should not be a config setting.

    INIT_PIPELINE = settings.settings.get("init_pipeline", True)
    json_msg = None
    if INIT_PIPELINE:
        async for msg in ws:
            debug_log("Auth", msg.data)
            try:
                json_msg = json.loads(msg.data)
            except:
                print("Bad message:",  msg)
                raise
            header_events.append(json_msg)
            if json_msg["event"] == "metadata_finished":
                break
    else:
        # This is a path for the old way of doing auth, which was to
        # send the auth data in the first message.
        #
        # It is untested, so we raise an error if it is used.
        #raise NotImplementedError("We have not tested auth backwards compatibility.")
        print("Running without an initialization pipeline / events. This is for")
        print("development purposes, and may not continue to be supported")
        msg = await ws.receive()
        json_msg = json.loads(msg.data)
        header_events.append(json_msg)

    first_event = header_events[0]
    event_metadata['source'] = first_event['source']

    # We authenticate the student
    event_metadata['auth'] = await learning_observer.auth.events.authenticate(
        request=request,
        headers=header_events,
        first_event=first_event,  # This is obsolete
        source=json_msg['source']
    )

    print(event_metadata['auth'])

    # We're now ready to make the pipeline.
    hostname = socket.gethostname();
    decoder_and_logger = event_decoder_and_logger(
        request,
        headers=header_events,
        metadata={
            'ip': request.remote,
            'host': request.headers.get('Host', ''),
            'user_agent': request.headers.get('User-Agent', ''),
            'x_real_ip': request.headers.get('X-Real-IP', ''),
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'session_count': COUNT,
            'pid': os.getpid(),
            'hostname': hostname,
            'hostip': socket.gethostbyname(hostname),
            'referer': request.headers.get('Referer', ''),
            'host': request.headers.get('Host', ''),
            'x-forwarded-for': request.headers.get('X-Forwarded-For', ''),
            'x-forwarded-host': request.headers.get('X-Forwarded-Host', '')
        },
        session={
            'student': event_metadata['auth']['safe_user_id'],
            'source': event_metadata['source']
        }
    )

    event_handler = await handle_incoming_client_event(metadata=event_metadata)

    # Handle events which we already received, if we needed to peak
    # ahead to authenticate user
    if not INIT_PIPELINE:
        for event in header_events:
            decoder_and_logger(event)
            await event_handler(request, event)

    # And continue to receive events
    async for msg in ws:
        # If web socket closed, we're done.
        if msg.type == aiohttp.WSMsgType.ERROR:
            debug_log('ws connection closed with exception %s' %
                  ws.exception())
            return

        # If we receive an unknown event type, we keep going, but we
        # print an error to the console. If we got some kind of e.g.
        # wonky ping or keep-alive or something we're unaware of, we'd
        # like to handle that gracefully.
        if msg.type != aiohttp.WSMsgType.TEXT:
            debug_log("Unknown event type: " + msg.type)

        client_event = decoder_and_logger(msg)
        await event_handler(request, client_event)

    debug_log('Websocket connection closed')
    return ws
