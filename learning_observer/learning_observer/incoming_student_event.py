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
import learning_observer.blacklist


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
        username=metadata.get("auth", {}).get("safe_user_id", "GUEST"),
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
    session={}
):
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
    if merkle_config := settings.feature_flag("merkle"):
        import merkle_store

        storage_class = merkle_store.STORES[merkle_config['store']]
        params = merkle_config.get("params", {})
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

    async def decode_and_log_event(events):
        '''
        Take an aiohttp web sockets message, log it, and return
        a clean event.
        '''
        async for msg in events:
            if isinstance(msg, dict):
                json_event = msg
            else:
                json_event = json.loads(msg.data)
            log_event.log_event(json_event, filename=filename)
            yield json_event
    return decode_and_log_event


async def failing_event_handler(*args, **kwargs):
    '''
    Give a proper AIO HTTP exception if we don't find an
    appropriate event handler or another error condition happens
    '''
    exception_text = "Event handler not set.\n" \
        "This probably means we do not have proper\n" \
        "metadata sent before the event stream"
    raise aiohttp.web.HTTPBadRequest(text=exception_text)


async def incoming_websocket_handler(request):
    '''This handles incoming WebSocket requests. We pass each event
    through minimal processing before it is added to a queue. Once
    we receive enough initial information (e.g. source and auth),
    we start processing each event in our queue through the reducers.
    '''
    debug_log("Incoming web socket connected")
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    lock_fields = {}
    authenticated = False
    event_handler = failing_event_handler

    decoder_and_logger = event_decoder_and_logger(request)

    async def process_message_from_ws():
        '''This function makes sure that the ws is an
        async generator for use in the processing pipeline
        '''
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.ERROR:
                debug_log(f"ws connection closed with exception {ws.exception()}")
                return
            if msg.type != aiohttp.WSMsgType.TEXT:
                debug_log("Unknown event type: " + msg.type)
            yield msg

        if ws.closed:
            debug_log(f'ws connection closed for reason {ws.close_code}')

    async def update_event_handler(event):
        '''We need source and auth ready before we can
        set up the `event_handler` and be ready to process
        events
        '''
        if not authenticated:
            return

        nonlocal event_handler
        if 'source' in lock_fields:
            debug_log('Updating the event_handler()')
            metadata = lock_fields.copy()
        else:
            metadata = event
        metadata['auth'] = authenticated
        event_handler = await handle_incoming_client_event(metadata=metadata)

    async def handle_auth_events(events):
        '''This method checks a single method for auth and
        updates our `lock_fields`. If we are unauthenticated,
        an error will be thrown and we ignore it.

        HACK The auth method expects a list of events to find
        specific auth events. Since we are yielding event by
        event, we check for auth on an individual event wrapped
        in a list. This workflow feels a little weird. We should
        re-evaluate the auth code.

        TODO We should consider stopping the loop if we receive
        enough events without receiving the authentication info.
        '''
        nonlocal authenticated
        backlog = []

        async for event in events:
            if 'auth' in event:
                raise ValueError('Auth already exists in event, someone may be trying to hack the system')
            if not authenticated:
                authenticated = await learning_observer.auth.events.authenticate(
                    request=request,
                    headers=[event],
                    first_event={},
                    source=''
                )
                await update_event_handler(event)
                backlog.append(event)
            else:
                while backlog:
                    prior_event = backlog.pop(0)
                    prior_event.update({'auth': authenticated})
                    yield prior_event
                event.update({'auth': authenticated})
                yield event

    async def decode_lock_fields(events):
        '''This function updates our overall lock_field
        object and sets those fields on other events.
        '''
        async for event in events:
            if event['event'] == 'lock_fields':
                if event['fields'].get('source', '') != lock_fields.get('source', ''):
                    lock_fields.update(event['fields'])
            else:
                event.update(lock_fields)
                yield event

    async def filter_blacklist_events(events):
        '''This function stops the event pipeline if sources
        should be blocked.
        '''
        async for event in events:
            # TODO implement the following function
            bl_status = learning_observer.blacklist.get_blacklist_status(event)
            if bl_status['action'] == learning_observer.blacklist.ACTIONS.TRANSMIT:
                yield event
            else:
                debug_log('Event is blacklisted.')
                await ws.send_json(bl_status)
                await ws.close()

    async def pass_through_reducers(events):
        '''Pass events through the reducers
        '''
        async for event in events:
            await event_handler(request, event)
            yield event

    async def process_ws_message_through_pipeline():
        '''Prepare each event we receive for processing
        '''
        events = process_message_from_ws()
        events = decoder_and_logger(events)
        events = decode_lock_fields(events)
        events = handle_auth_events(events)
        events = filter_blacklist_events(events)
        events = pass_through_reducers(events)
        # empty loop to start the generator pipeline
        async for event in events:
            pass
        debug_log('We are done passing events through the pipeline.')

    # process websocket messages and begin executing events from the queue
    await process_ws_message_through_pipeline()

    return ws
