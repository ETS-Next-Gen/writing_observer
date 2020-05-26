import datetime
import json
import time
import traceback
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


async def student_event_pipeline(parsed_message):
    client_source = parsed_message["client"]["source"]
    if client_source in stream_analytics.analytics_modules:
        debug_log("Processing PubSub message {event} from {source}".format(
            event=parsed_message["client"]["event"], source=client_source
        ))
        analytics_module = stream_analytics.analytics_modules[client_source]
        event_processor = analytics_module['event_processor']
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
    else:
        debug_log("Unknown event source" + str(parsed_message))
        return []


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


async def handle_incoming_client_event():
    '''
    Common handler for both Websockets and AJAX events.

    We do a reduce through the event pipeline, and forward on to
    the pubsub for aggregation on the dashboard side.
    '''
    debug_log("Connecting to pubsub source")
    pubsub_client = await pubsub.pubsub_send()
    debug_log("Connected")

    async def handler(request, client_event):
        debug_log("Compiling event for PubSub: "+client_event["event"])
        event = {
            "client": client_event,
            "server": compile_server_data(request)
        }

        log_event.log_event(event)
        log_event.log_event(
            json.dumps(event, sort_keys=True),
            "incoming_websocket", preencoded=True, timestamp=True)
        print(pubsub_client)
        outgoing = await student_event_pipeline(event)
        for item in outgoing:
            await pubsub_client.send_event(mbody=json.dumps(item, sort_keys=True))
            debug_log("Sent item to PubSub triggered by: "+client_event["event"])
    return handler


async def incoming_websocket_handler(request):
    '''
    This handles incoming WebSockets requests. It does some minimal
    processing on them, and then relays them on via PubSub to be
    aggregated. It also logs them.
    '''
    debug_log("Incoming web socket connected")
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    event_handler = await handle_incoming_client_event()

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
            if json_msg["event"] == "metadata-finished":
                break
            elif json_msg["event"] == "google_chrome_identity":
                headers["chrome_identity"] = json_msg["chrome_identity"]
            elif json_msg["event"] == "local_storage":
                headers["local_storage"] = json_msg["local_storage"]
        event_metadata['headers'].update(headers)
        print(headers)
        print(event_metadata)
        #  init = [await ws.receive_json(), await ws.receive_json(), await ws.receive_json()]

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
