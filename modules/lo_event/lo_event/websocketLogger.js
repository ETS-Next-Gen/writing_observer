import { Queue } from './queue.js';
import { WebSocket } from 'ws';
import { BlockError } from './blacklist.js';

export function websocketLogger (server, storage) {
  /*
     Log to web socket server.
  */
  let socket, preauth, postauth, preauth_sent, postauth_sent;
  const queue = new Queue('websocketLogger');
  let blockerror;

  function newWebsocket () {
    preauth_sent = false;
    postauth_sent = false;
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

  function prepareSocket () {
    // Send the server the user info. This might not always be available.
    let event;

    event = { local_storage: {} }
    console.log(event);

    dequeue();
  }

  function receiveMessage (event) {
    const response = JSON.parse(event.data);

    switch (response.status) {
      case 'blocklist':
        console.log("Received block error");
        blockerror = new BlockError(
          response.message,
          response.time_limit,
          response.action
        );
      default:
        console.log('auth has not yet occured');
        break;
    }
    dequeue();
  }

  function checkMetadata() {
    if(preauth && !preauth_sent) {
      socket.send(JSON.stringify({ ...preauth, event_type: "lock_fields" }));
      preauth_sent = true;
    }
    if(postauth && !postauth_sent) {
      socket.send(JSON.stringify( { ...postauth, event_type: "lock_fields"} ));
      postauth_sent = true;
    }
  }

  async function dequeue () {
    console.log('dequeuing');
    if (socket === null) {
      // Do nothing. We're reconnecting.
      console.log('Event squelched; reconnecting');
    } else if (socket.readyState === socket.OPEN) {
      console.log('sending messages in queue', queue.count());
      while (await queue.count() > 0) {
        const event = await queue.dequeue();
        checkMetadata();
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
      await delay(1000);
      console.log('Re-opening connection');
      socket = newWebsocket();
    }
  }

  function ws_log_data(data) {
    if(blockerror) {
      console.log("Throwing block error");
      const b = blockerror;
      blockerror = null;
      throw b;
    }
    console.log('queue data', data);
    queue.enqueue(data);
    dequeue();
  }

  ws_log_data.preauth = function(metadata) {
    preauth = metadata;
  }

  ws_log_data.postauth = function(metadata) {
    postauth = metadata;
  }

  return ws_log_data;
}
