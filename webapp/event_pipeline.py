import datetime
import json
import time
import traceback
import urllib.parse
import uuid

import aiohttp

import log_event

import pubsub            # Pluggable pubsub subsystem
import stream_analytics  # Individual analytics modules

from log_event import debug_log


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
    if client_source not in stream_analytics.analytics_modules:
        debug_log("Unknown event source" + str(parsed_message))
        raise Exception("Unknown event source")
    analytics_module = stream_analytics.analytics_modules[client_source]
    # Create an event processor for this user
    event_processor = analytics_module['event_processor'](metadata)

    async def pipeline(parsed_message):
        '''
        And this is the pipeline itself. It takes messages, processes them,
        and informs consumers when there is new data.
        '''
        debug_log("Processing PubSub message {event} from {source}".format(
            event=parsed_message["client"]["event"], source=client_source
        ))
        try:
            processed_analytics = await event_processor(parsed_message)
        except Exception as e:
            traceback.print_exc()
            filename = "logs/critical-error-{ts}-{rnd}.tb".format(
                ts=datetime.datetime.now().isoformat(),
                rnd=uuid.uuid4().hex
            )
            fp = open(filename, "w")
            fp.write(json.dumps(parsed_message, sort_keys=True, indent=2))
            fp.write("\nTraceback:\n")
            fp.write(traceback.format_exc())
            fp.close()
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
            print("FIXME: Should return list")
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
    the pubsub for aggregation on the dashboard side.
    '''
    debug_log("Connecting to pubsub source")
    pubsub_client = await pubsub.pubsub_send()
    debug_log("Connected")

    pipeline = await student_event_pipeline(metadata=metadata)

    async def handler(request, client_event):
        debug_log("Compiling event for PubSub: "+client_event["event"])
        event = {
            "client": client_event,
            "server": compile_server_data(request),
            "metadata": metadata
        }

        log_event.log_event(event)
        log_event.log_event(
            json.dumps(event, sort_keys=True),
            "incoming_websocket", preencoded=True, timestamp=True)
        print(pubsub_client)
        outgoing = await pipeline(event)
        for item in outgoing:
            await pubsub_client.send_event(mbody=json.dumps(item, sort_keys=True))
            debug_log("Sent item to PubSub triggered by: "+client_event["event"])
    return handler


async def dummy_auth(metadata):
    '''
    This is a dummy authentication function. It trusts the metadata in the web
    socket without auth/auth.

    Our thoughts are that the auth metadata ought to contain:
    1. Whether the user was authenticated (`sec` field):
       * `authenticated` -- we trust who they are
       * `unauthenticated` -- we think we know who they are, without security
       * `guest` -- we don't know who they are
    2. Providence: How they were authenticated (if at all), or how we believe
       they are who they are.
    3. `user_id` -- a unique user identifier
    '''
    if 'local_storage' in metadata and 'user-tag' in metadata['local_storage']:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ls-"+metadata['local_storage']['user_tag'],
            'providence': 'lsu'  # local storage, unauthenticated
        }
    elif 'chrome_identity' in metadata:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "gc-"+metadata['chrome_identity']['email'],
            'providence': 'gcu'  # Google Chrome, unauthenticated
        }
    elif 'test_framework_fake_identity' in metadata:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ts-"+metadata['test_framework_fake_identity'],
            'providence': 'tsu'  # Test Script, unauthenticated
        }
    else:
        auth_metadata = {
            'sec': 'none',
            'user_id': 'guest',
            'safe_user_id': 'guest',
            'providence': 'guest'
        }

    # We don't know where user IDs will come from.
    #
    # We'd like a version of the user ID which can be encoded in keys,
    # given to SQL, etc. without opening up security holes.
    #
    # We also want to avoid overlapping UIDs between sources. For
    # example, we don't want an attack where e.g. a user carefully
    # creates an account on one auth provide to collide with a pre-existing
    # account on another auth provider. So we append providence.
    if "safe_user_id" not in auth_metadata:
        auth_metadata['safe_user_id'] = "{src}-{uid}".format(
            src=auth_metadata["providence"],
            uid=urllib.parse.quote_plus(
                auth_metadata['user_id'],
                safe='@'  # Keep emails more readable
            )
        )
    return auth_metadata

auth = dummy_auth


async def incoming_websocket_handler(request):
    '''
    This handles incoming WebSockets requests. It does some minimal
    processing on them, and then relays them on via PubSub to be
    aggregated. It also logs them.
    '''
    debug_log("Incoming web socket connected")
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    # For now, we receive two packets to initialize:
    # * Chrome's identity information
    # * browser.storage identity information
    event_metadata = {'headers': {}}
    INIT_PIPELINE = True
    if INIT_PIPELINE:
        headers = {}
        async for msg in ws:
            json_msg = json.loads(msg.data)
            print(json_msg)
            print(json_msg["event"])
            print(json_msg["event"] == "metadata_finished")
            if json_msg["event"] == "metadata_finished":
                break
            elif json_msg["event"] == "chrome_identity":
                headers["chrome_identity"] = json_msg["chrome_identity"]
            elif json_msg["event"] == "local_storage":
                headers["local_storage"] = json_msg["local_storage"]
            elif json_msg["event"] == "test_framework_fake_identity":
                headers["test_framework_fake_identity"] = json_msg["user_id"]
            if 'source' in json_msg:
                event_metadata['source'] = json_msg['source']
        event_metadata['headers'].update(headers)

    event_metadata['auth'] = await auth(headers)
    print(event_metadata)

    event_handler = await handle_incoming_client_event(metadata=event_metadata)

    async for msg in ws:
        debug_log("Web socket message received")
        if msg.type == aiohttp.WSMsgType.TEXT:
            client_event = json.loads(msg.data)
            debug_log(
                "Dispatching incoming websocket event: " +
                client_event['event']
            )
            await event_handler(request, client_event)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    debug_log('Websocket connection closed')
    return ws


async def outgoing_websocket_handler(request):
    '''
    This pipes analytics back to the browser. It:
    1. Handles incoming PubSub connections
    2. Sends it back to the browser

    TODO: Cleanly handle disconnects
    '''
    debug_log('Outgoing analytics web socket connection')
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    pubsub_client = await pubsub.pubsub_receive()
    debug_log("Awaiting PubSub messages")
    while True:
        message = await pubsub_client.receive()
        debug_log("PubSub event received")
        log_event.log_event(
            message, "incoming_pubsub", preencoded=True, timestamp=True
        )
        log_event.log_event(
            message,
            "outgoing_analytics", preencoded=True, timestamp=True)
        await ws.send_str(message)
    await ws.send_str("Done")
