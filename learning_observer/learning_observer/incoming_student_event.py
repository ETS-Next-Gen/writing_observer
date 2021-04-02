'''
This has event handlers for incoming student events.

These should come in over a websocket. We support AJAX too, since it's
nice for debugging. This should never be used in production.

We:
* Authenticate (minimally, for now, see docs)
* Run these through a set of reducers
* Optionally, notify via a pubsub of new data
'''

import datetime
import json
import time
import traceback
import urllib.parse
import uuid

import aiohttp

import log_event
import paths

import authutils         # Encoded / decode user IDs
import pubsub            # Pluggable pubsub subsystem
import stream_analytics  # Individual analytics modules

import settings

from log_event import debug_log

import learning_observer.exceptions


stream_analytics.init()


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
    if client_source not in stream_analytics.student_reducer_modules():
        debug_log("Unknown event source: " + str(client_source))
        debug_log("Known sources: " + repr(stream_analytics.student_reducer_modules().keys()))
        raise learning_observer.exceptions.SuspiciousOperation("Unknown event source")
    analytics_modules = stream_analytics.student_reducer_modules()[client_source]
    # Create an event processor for this user
    # TODO: This should happen in parallel: https://stackoverflow.com/questions/57263090/async-list-comprehensions-in-python
    event_processors = [await am['student_event_reducer'](metadata) for am in analytics_modules]

    async def pipeline(parsed_message):
        '''
        And this is the pipeline itself. It takes messages, processes them,
        and informs consumers when there is new data.
        '''
        debug_log("Processing PubSub message {event} from {source}".format(
            event=parsed_message["client"]["event"], source=client_source
        ))

        # Try to run a message through all event processors.
        #
        # To do: Finer-grained exception handling. Right now, if we break, we don't run
        # through remaining processors.
        try:
            print(event_processors)
            processed_analytics = [await ep(parsed_message) for ep in event_processors]
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
        debug_log("Compiling event for PubSub: " + client_event["event"])
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

        # We're currently polling on the other side.
        #
        # Leaving this code in without a receiver gives us a massive
        # memory leak, so we've commented it out until we do plan to
        # subscribe again.
        if False:
            for item in outgoing:
                await pubsub_client.send_event(
                    mbody=json.dumps(item, sort_keys=True)
                )
                debug_log(
                    "Sent item to PubSub triggered by: " + client_event["event"]
                )
    return handler


async def dummy_auth(metadata):
    '''
    TODO: Replace with real auth
    TODO: Allow configuring auth methods in settings file
    TODO: See about client-side oauth on Chromebooks
    TODO: Allow configuring authentication methods based on event
    type (e.g. require auth for writing, but not for dynamic assessment)

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
            'user_id': "ls-" + metadata['local_storage']['user_tag'],
            'providence': 'lsu'  # local storage, unauthenticated
        }
    elif 'chrome_identity' in metadata:
        gc_uid = authutils.google_id_to_user_id(metadata['chrome_identity']['id'])
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': gc_uid,
            'safe_user_id': gc_uid,
            'providence': 'gcu'  # Google Chrome, unauthenticated
        }
    elif "hash_identity" in metadata:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ts-" + metadata['hash_identity'],
            'providence': 'mch'  # Math contest hash -- toying with plug-in archicture
        }
    elif 'test_framework_fake_identity' in metadata:
        auth_metadata = {
            'sec': 'unauthenticated',
            'user_id': "ts-" + metadata['test_framework_fake_identity'],
            'providence': 'tsu'  # Test Script, unauthenticated
        }
    else:
        auth_metadata = {
            'sec': 'none',
            'user_id': 'guest',
            'safe_user_id': 'guest',
            'providence': 'guest'
        }

    # This is a bit of encoding logic to generically encode IDs from
    # unknown sources. We want to avoid the problem of Little Bobby
    # Tables (https://xkcd.com/327/).
    #
    # It's not clear this is needed long-term (we put this in when we
    # were using Google emails rather than numeric IDs), but we're
    # keeping it here for now for the test data sources. This just
    # generically sanitizes everything in case we either missed
    # something above, or just want to have a sane default before
    # implementing something fancy.
    #
    # We also want to avoid overlapping UIDs between sources. For
    # example, we don't want an attack where e.g. a user carefully
    # creates an account on one auth provide to collide with a
    # pre-existing account on another auth provider. So we append
    # providence. Note that we don't want to do this twice (so
    # `authutils` does this already for Google)
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
            print("Auth", msg)
            json_msg = json.loads(msg.data)
            # print(json_msg)
            # print(json_msg["event"])
            if 'source' in json_msg:
                event_metadata['source'] = json_msg['source']
            # print(json_msg["event"] == "metadata_finished")
            if json_msg["event"] == "metadata_finished":
                break
            elif json_msg["event"] == "chrome_identity":
                headers["chrome_identity"] = json_msg["chrome_identity"]
            elif json_msg["event"] == "hash_auth":
                headers["hash_identity"] = json_msg["hash"]
            elif json_msg["event"] == "local_storage":
                try:
                    headers["local_storage"] = json_msg["local_storage"]
                except Exception:
                    print(json_msg)
                    raise
            elif json_msg["event"] == "test_framework_fake_identity":
                headers["test_framework_fake_identity"] = json_msg["user_id"]
        event_metadata['headers'].update(headers)

        event_metadata['auth'] = await auth(headers)
        # print(event_metadata)

    event_handler = await handle_incoming_client_event(metadata=event_metadata)

    async for msg in ws:
        debug_log("Web socket message received")
        if msg.type == aiohttp.WSMsgType.TEXT:
            client_event = json.loads(msg.data)
            debug_log(
                "Dispatch incoming ws event: " + client_event['event']
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
