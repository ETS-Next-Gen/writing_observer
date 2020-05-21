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
    Common handler for both Websockets and AJAX events. This is just a thin
    pipe to pubsub with some logging.
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
        await pubsub_client.send_event(mbody=json.dumps(event, sort_keys=True))
        debug_log("Sent event to PubSub: "+client_event["event"])
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


async def student_event_pipeline(parsed_message):
    client_source = parsed_message["client"]["source"]
    if True:
        if client_source in stream_analytics.analytics_modules:
            debug_log("Processing PubSub message {event} from {source}".format(
                event=parsed_message["client"]["event"], source=client_source
            ))
            analytics_module = stream_analytics.analytics_modules[client_source]
            event_processor = analytics_module['event_processor']
            try:
                processed_analytics = event_processor(parsed_message)
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
            if processed_analytics is None:
                debug_log("No updates")
                return []
            # Transitional code.
            #
            # We'd eventually like to return only lists of outgoing
            # events. No event means we send back [] For now, our
            # modules return `None` to do nothing, events, or lists of
            # events.
            if not isinstance(processed_analytics, list):
                processed_analytics = [processed_analytics]
            return processed_analytics
        else:
            debug_log("Unknown event source" + str(parsed_message))
            return []


async def outgoing_websocket_handler(request):
    '''
    This pipes analytics back to the browser. It:
    1. Handles incoming PubSub connections
    2. Processes the data
    3. Sends it back to the browser

    TODO: Cleanly handle disconnects
    '''
    debug_log('Outgoing analytics web socket connection')
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    pubsub_client = await pubsub.pubsub_receive()
    debug_log("Awaiting PubSub messages")
    while True:
        message = await pubsub_client.receive()
        parsed_message = json.loads(message)
        debug_log("PubSub event received: "+parsed_message['client']['event'])
        log_event.log_event(
            message, "incoming_pubsub", preencoded=True, timestamp=True
        )
        client_source = parsed_message["client"]["source"]
        processed_analytics = await student_event_pipeline(parsed_message)
        for outgoing_event in processed_analytics:
            log_event.log_event(
                json.dumps(outgoing_event, sort_keys=True),
                "outgoing_analytics", preencoded=True, timestamp=True)
            message = json.dumps(outgoing_event, sort_keys=True)
            await ws.send_str(message)
    await ws.send_str("Done")
