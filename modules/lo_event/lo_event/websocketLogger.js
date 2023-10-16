import { Queue } from './queue.js';
import { WebSocket } from 'ws';

export function websocketLogger (server, storage) {
  /*
     Log to web socket server.
  */
  let socket;
  let state = new Set();
  const queue = new Queue('websocketLogger');

  function newWebsocket () {
    socket = new WebSocket(server);
    socket.onopen = prepareSocket;
    socket.onerror = function (e) {
      console.log('Could not connect');
      let event = { issue: 'Could not connect' };
      // event = add_event_metadata('warning', event)
      event = JSON.stringify(event);
      queue.enqueue(event);
    }
    socket.onclose = function (e) {
      console.log('Lost connection');
      let event = { issue: 'Lost connection', code: e.code };
      // event = add_event_metadata('warning', event)
      event = JSON.stringify(event);
      queue.enqueue(event);
    }
    socket.onmessage = receiveMessage;
    return socket;
  }

  socket = newWebsocket();

  function areWeDone () {
    console.log('are we done yet?');
    if (!state.has('ready')) {
      state.add('ready');
      dequeue();
    }
    return true;
  }

  function prepareSocket () {
    // Send the server the user info. This might not always be available.
    state = new Set();
    let event;

    event = { local_storage: {} }
    console.log(event);
    // event = add_event_metadata('local_storage', event)
    //socket.send(JSON.stringify(event)); // do we need this to send right here, we aren't fully ready
    state.add('local_storage');
    areWeDone();
  }

  function receiveMessage (event) {
    const response = JSON.parse(event.data);

    switch (response.status) {
      case 'allow':
        state.add('allow');
        break
      case 'deny':
        state.add('deny');
        // TODO handle any deny status
        break
      default:
        console.log('auth has not yet occured');
        break;
    }
    areWeDone();
  }

  async function dequeue () {
    console.log('dequeuing');
    if (socket === null) {
      // Do nothing. We're reconnecting.
      console.log('Event squelched; reconnecting');
    } else if (socket.readyState === socket.OPEN &&
      state.has('ready')) {
      console.log('sending messages in queue', queue.count());
      while (await queue.count() > 0) {
        const event = await queue.dequeue();
        console.log('about to send', event);
        socket.send(event); /* TODO: We should do receipt confirmation before dropping events */
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
      state = new Set();
      await delay(1000);
      console.log('Re-opening connection');
      socket = newWebsocket();
    }
  }

  function ws_log_data(data) {
    console.log('queue data', data);
    queue.enqueue(data);
    dequeue();
  }

  ws_log_data.preauth = function(metadata) {
    // TODO:
    // We want to send events with an event type of 'set_metadata' containing the metadata
  }

  ws_log_data.postauth = function() {
    // TODO:
    // We want to acknowledge any auth message.
    // If we're locked, we want to raise an exception from `blacklist.js` which will be handled by `lo_event`
    // We want to send events with an event type of 'set_metadata' containing the metadata
  }

  return ws_log_data;
}
