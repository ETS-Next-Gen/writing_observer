import { Queue } from './queue.js';
import { BlockError } from './disabler.js';
import { profileInfoWrapper, backoff } from './util.js';
import * as debug from './debugLog.js';
import * as util from './util.js';

export function websocketLogger (server) {
  /*
     Log to web socket server.
  */
  let socket;
  let WS;
  const queue = new Queue('websocketLogger');
  let blockerror;
  let firstConnection = true;
  let metadata = {};

  function newWebsocket () {
    socket = new WS(server);
    socket.onopen = prepareSocket;
    socket.onerror = function (e) {
      debug.error('Could not connect to websocket', e);
    };
    socket.onclose = onClose;
    socket.onmessage = receiveMessage;
    return socket;
  }

  function prepareSocket () {
    // TODO fetch local storage items here
    const event = { local_storage: {} };
    console.log(event);
    if (!firstConnection) {
      profileInfoWrapper().then((result) => {
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
          queue.enqueue(JSON.stringify({ event: 'metadata_finished' }));
        }
      });
    } else {
      firstConnection = false;
    }

    dequeue();
  }

  function receiveMessage (event) {
    const response = JSON.parse(event.data);

    switch (response.status) {
      case 'blocklist':
        debug.info('Received block error from server');
        blockerror = new BlockError(
          response.message,
          response.time_limit,
          response.action
        );
        break;
      default:
        // console.log('auth has not yet occured');
        break;
    }
    // dequeue();
  }

  function onClose (event) {
    debug.error('Lost connection to websocket', event);
    backoff(() => {
      checkForBlockError();
      socket = newWebsocket();
      return socket;
    }, 'Unable to reconnect to websocket server').then(
      // we are connected again
    ).catch(
      // we were unable to connect either from the block error
      // or unable to connect to the websocket we should stop
      // trying entirely.
    );
  }

  // TODO Remove this commented out code:
  // this is the old way of dequeueing while we figure out a better structure

  // async function dequeue () {
  //   if (socket === null) {
  //     // Do nothing. We're reconnecting.
  //     console.log('Event squelched; reconnecting');
  //   } else if (socket.readyState === socket.OPEN) {
  //     while (await queue.count() > 0) {
  //       try {
  //         const event = await queue.nextItem();
  //         socket.send(event); /* TODO: We should do receipt confirmation before dropping events */
  //       } catch (error) {
  //         debug.error('Error during dequeue', error);
  //       }
  //     }
  //   } else if ((socket.readyState === socket.CLOSED) || (socket.readyState === socket.CLOSING)) {
  //     /*
  //       If we lost the connection, we wait a second and try to open it again.

  //       Note that while socket is `null` or `CONNECTING`, we don't take either
  //       branch -- we just queue up events. We reconnect after 1 second if closed,
  //       or dequeue events if open.
  //     */
  //     console.log('Re-opening connection in 1s');
  //     socket = null;
  //     await delay(1000);
  //     console.log('Re-opening connection');
  //     socket = newWebsocket();
  //   } else if (socket.readyState === socket.CONNECTING) {
  //     console.log('connecting still');
  //   }
  // }

  async function sendItem () {
    // will this wait until the next item is available?
    try {
      console.log('awaiting next item in queue');
      const event = await queue.dequeue();
      if (event !== null) {
        socket.send(event);
      }
    } catch (error) {
      debug.error('Unable to dequeue event in websocketLogger', error);
    }
  }

  const dequeue = util.once(async function () {
    // initialization step

    while (true) {
      console.log('iterating over dequeue');
      if (socket === null) {
        // do nothing possibly break out of loop
      }

      // allowed to stream
      if (socket.readyState === socket.OPEN) {
        await sendItem();
      }

      // termination dequeue loop
      if ((socket.readyState === socket.CLOSING) || (socket.readyState === socket.CLOSED)) {
        return;
      }
    }
  });

  function checkForBlockError () {
    if (blockerror) {
      console.log('Throwing block error');
      const b = blockerror;
      blockerror = null;
      throw b;
    }
  }

  function wsLogData (data) {
    checkForBlockError();
    queue.enqueue(data);
    // dequeue();
  }

  wsLogData.init = async function (metadata) {
    if (typeof WebSocket === 'undefined') {
      debug.info('Importing ws');
      WS = (await import('ws')).WebSocket;
    } else {
      debug.info('Using built-in websocket');
      WS = WebSocket;
    }
    socket = newWebsocket();
  };

  wsLogData.setField = function (data) {
    metadata = { ...metadata, ...JSON.parse(data) };
    queue.enqueue(data);
  };

  return wsLogData;
}
