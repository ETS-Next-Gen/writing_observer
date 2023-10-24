import { Queue } from './queue.js';
import { BlockError } from './disabler.js';
import { delay } from './util.js';
import * as debug from './debugLog.js';

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
      let event = { issue: 'Could not connect' };
      event = JSON.stringify(event);
      queue.enqueue(event);
    };
    socket.onclose = function (e) {
      debug.error('Lost connection to websocket', e);
      let event = { issue: 'Lost connection', code: e.code };
      event = JSON.stringify(event);
      queue.enqueue(event);
    };
    socket.onmessage = receiveMessage;
    return socket;
  }

  function prepareSocket () {
    const event = { local_storage: {} };
    console.log(event);
    if (!firstConnection) {
      // queue.prepend(metadata);
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
        console.log('auth has not yet occured');
        break;
    }
    dequeue();
  }

  async function dequeue () {
    if (socket === null) {
      // Do nothing. We're reconnecting.
      console.log('Event squelched; reconnecting');
    } else if (socket.readyState === socket.OPEN) {
      while (await queue.count() > 0) {
        try {
          const event = await queue.nextItem();
          socket.send(event); /* TODO: We should do receipt confirmation before dropping events */
        } catch (error) {
          debug.error('Error during dequeue', error);
        }
      }
    } else if ((socket.readyState === socket.CLOSED) || (socket.readyState === socket.CLOSING)) {
      /*
        If we lost the connection, we wait a second and try to open it again.

        Note that while socket is `null` or `CONNECTING`, we don't take either
        branch -- we just queue up events. We reconnect after 1 second if closed,
        or dequeue events if open.
      */
      console.log('Re-opening connection in 1s');
      socket = null;
      await delay(1000);
      console.log('Re-opening connection');
      socket = newWebsocket();
    } else if (socket.readyState === socket.CONNECTING) {
      console.log('connecting still');
    }
  }

  function wsLogData (data) {
    if (blockerror) {
      console.log('Throwing block error');
      const b = blockerror;
      blockerror = null;
      throw b;
    }
    queue.enqueue(data);
    dequeue();
  }

  wsLogData.init = async function (metadata) {
    if (typeof WebSocket === 'undefined') {
      console.log('Importing ws');
      WS = (await import('ws')).WebSocket;
    } else {
      console.log('Using built-in websocket');
      WS = WebSocket;
    }
    socket = newWebsocket();
  };

  wsLogData.setField = function (data) {
    metadata = { ...metadata, ...data };
    queue.enqueue(data);
  };

  return wsLogData;
}
