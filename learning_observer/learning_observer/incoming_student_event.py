'''
This has event handlers for incoming student events.

These should come in over a websocket. We support AJAX too, since it's
nice for debugging. This should never be used in production.

We:
* Authenticate (minimally, for now, see docs)
* Run these through a set of reducers
* Optionally, notify via a pubsub of new data
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
# import learning_observer.pubsub as pubsub                    # Pluggable pubsub subsystem
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
        and informs consumers when there is new data.
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
        # To do: Finer-grained exception handling. Right now, if we break, we don't run
        # through remaining processors.
        try:
            processed_analytics = []
            for am in analytics_modules:
                debug_log("Scope", am['scope'])
                args = {}
                skip = False
                for field in am['scope']:
                    if isinstance(field, learning_observer.stream_analytics.helpers.EventField):
                        debug_log("event", parsed_message)
                        debug_log("field", field)
                        client_event = parsed_message.get('client', {})
                        if field.event not in client_event:
                            debug_log(field.event, "not found")
                            skip = True
                        args[field.event] = client_event.get(field.event)
                if not skip:
                    debug_log("args", args)
                    processed_analytics.append(await am['reducer_partial'](parsed_message, **args))
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
        if processed_analytics is None:
            debug_log("No updates")
            return []
        # Transitional code.
        #
        # We'd eventually like to return only lists of outgoing
        # events. No event means we send back [] For now, our
        # modules return `None` to do nothing, events, or lists of
        # events.
        #
        # That's a major refactor away. We'd like to pass in lists /
        # iterators of incoming events so we can handle microbatches,
        # and generate lists of outgoing events too.
        if not isinstance(processed_analytics, list):
            debug_log("FIXME: Should return list")
            processed_analytics = [processed_analytics]
        return processed_analytics
    return pipeline


async def ajax_event_request(request):
    '''
    This is the original HTTP AJAX logging API. It is deprecated in
    favor of WebSockets.

    Using AJAX opens a new connection to pubsub every time, and so
    would be too slow for production use. We could have a global
    shared connection connection, but we anticipate this might run
    into scalability issues with some pubsub systems (depending on
    whether different users can share a connection, or whether
    each user has their own sender account).

    In either case, this is handler is helpful for small-scale debugging.
    '''
    debug_log("AJAX Request received")
    client_event = await request.json()
    handler = await handle_incoming_client_event()
    await handler(request, client_event)
    return aiohttp.web.Response(text="Acknowledged!")


async def handle_incoming_client_event(metadata):
    '''
    Common handler for both Websockets and AJAX events.

    We do a reduce through the event pipeline, and forward on to
    for aggregation on the dashboard side.
    '''
    # We used to do a pubsub model, where we'd update teacher
    # dashboards with new data. With typing, period aggregated
    # updates are more efficient, since we have many keystrokes
    # per second
    PUBSUB = False

    if PUBSUB:
        debug_log("Connecting to pubsub source")
        pubsub_client = await pubsub.pubsub_send()
        debug_log("Connected")

    pipeline = await student_event_pipeline(metadata=metadata)
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
        # Log the same thing with a time stamp. We really don't want this second log. We had these both for debugging....
        log_event.log_event(
            json.dumps(event, sort_keys=True),
            "incoming_websocket", preencoded=True, timestamp=True)
        if PUBSUB:
            debug_log("Pubsub client", pubsub_client)
        outgoing = await pipeline(event)

        # We're currently polling on the other side.
        #
        # Leaving this code in without a receiver gives us a massive
        # memory leak, so we've commented it out until we do plan to
        # subscribe again.
        if PUBSUB:
            for item in outgoing:
                await pubsub_client.send_event(
                    mbody=json.dumps(item, sort_keys=True)
                )
                debug_log(
                    "Sent item to PubSub triggered by: " + client_event["event"]
                )
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
    processing on them. It used to relays them on via PubSub to be
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
            debug_log("Auth", msg)
            json_msg = json.loads(msg)
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

    event_handler = None
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
