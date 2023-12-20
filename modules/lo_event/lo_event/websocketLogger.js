import { Queue } from './queue.js';
import * as disabler from './disabler.js';
import * as util from './util.js';
import * as debug from './debugLog.js';

export function websocketLogger (server) {
  /*
    This is a pretty complex logger, which sends events over a web
    socket. Most of the complexity comes from reconnections, retries,
    etc. and the need to keep robust queues, as well as the need be
    robust about queuing events before we have a socket open or during
    a network failure.
  */
  let socket; // Our actual socket used to send and receive data.
  let WSLibrary; // For compatibility between node and browser, this either points to the browser WebSocket or to a compatibility library.
  const queue = new Queue('websocketLogger');
  // This holds an exception, if we're blacklisted, between the web
  // socket and the API. We generate this when we receive a message,
  // which is not a helpful place to raise the exception from, so we
  // keep this around until we're called from the client, and then we
  // raise it there.
  let blockerror;
  let firstConnection = true;
  let metadata = {};

  function calculateExponentialBackoff (n) {
    return Math.min(1000 * Math.pow(2, n), 1000 * 60 * 15);
  }

  let failures = 0;
  let READY = false;
  let wsFailureResolve = null;
  let wsFailurePromise = null;
  let wsConnectedResolve = null;

  async function startWebsocketConnectionLoop () {
    while (true) {
      const connected = await newWebsocket();
      if (!connected) {
        failures++;
        await util.delay(calculateExponentialBackoff(failures));
      } else {
        READY = true;
        failures = 0;
        await socketClosed();
        READY = false;
      }
    }
  }

  function socketClosed () { return wsFailurePromise; }

  function newWebsocket () {
    socket = new WSLibrary(server);
    wsFailurePromise = new Promise((resolve, reject) => {
      wsFailureResolve = resolve;
    });
    const wsConnectedPromise = new Promise((resolve, reject) => {
      wsConnectedResolve = resolve;
    });
    socket.onopen = () => { prepareSocket(); wsConnectedResolve(true); };
    socket.onerror = function (e) {
      debug.error('Could not connect to websocket', e);
      wsConnectedResolve(false);
      wsFailureResolve();
    };
    socket.onclose = () => { wsConnectedResolve(false); wsFailureResolve(); };
    socket.onmessage = receiveMessage;
    return wsConnectedPromise;
  }

  function prepareSocket () {
    // TODO fetch local storage items here
    const event = { local_storage: {} };
    console.log(event);
    /**
     * The extension expects some auth and metadata before processing events
     * through the reducers. The first time this data is sent is handled by
     * `lo_event.js`. If the websocket disconnects and reconnects without
     * restarting the main `lo_event` module, then we need to resend the
     * auth and metadata.
     *
     * This code handles adding the auth and metadata to the processing queue
     * on all but the initial connection.
     */
    if (!firstConnection) {
      util.profileInfoWrapper().then((result) => {
        if (Object.keys(result).length > 0) {
          /**
           * HACK: this code is wrong
           * This is for backwards compatibility for the old way of handling auth.
           * This is scaffolding as we are changing how we handle lock_fields,
           * metedata, auth, etc. We should not be needing to call `profileInfoWrapper`
           * as that has been abstracted up many levels. The `metedata_finished` and
           * `chrome_identity` events should be removed when the server-side code
           * is updated and we have a new handshake protocol.
          */
          queue.enqueue(JSON.stringify(metadata));
          queue.enqueue(JSON.stringify({ event: 'chrome_identity', chrome_identity: result }));
        }
      });
    } else {
      firstConnection = false;
    }

    queue.startDequeueLoop({
      initialize: waitForWSReady,
      shouldDequeue: waitForWSReady,
      onDequeue: socketSend
    });
  }

  async function socketSend (item) {
    socket.send(item);
  }

  async function waitForWSReady () {
    return await util.backoff(() => (READY));
  }

  function receiveMessage (event) {
    const response = JSON.parse(event.data);

    switch (response.status) {
      case 'blocklist':
        debug.info('Received block error from server');
        blockerror = new disabler.BlockError(
          response.message,
          response.time_limit,
          response.action
        );
        break;
      default:
        debug.info(`Received response we do not yet handle: ${response}`);
        break;
    }
  }

  function checkForBlockError () {
    if (blockerror) {
      console.log('Throwing block error');
      const b = blockerror;
      blockerror = null;
      socket.close();
      throw b;
    }
  }

  function wsLogData (data) {
    checkForBlockError();
    queue.enqueue(data);
  }

  wsLogData.init = async function () {
    if (typeof WebSocket === 'undefined') {
      debug.info('Importing ws');
      WSLibrary = (await import('ws')).WebSocket;
    } else {
      debug.info('Using built-in websocket');
      WSLibrary = WebSocket;
    }
    startWebsocketConnectionLoop();
  };

  wsLogData.setField = function (data) {
    metadata = { ...metadata, ...JSON.parse(data) };
    queue.enqueue(data);
  };

  return wsLogData;
}
