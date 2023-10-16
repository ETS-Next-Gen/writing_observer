import { WebSocketServer } from 'ws';
import { storage } from '../lo_event/storage.js'
import * as util from '../lo_event/util.js'

import * as lo_event from '../lo_event/lo_event.js'
import * as websocketLogger from '../lo_event/websocketLogger.js'

console.log("Launching server");

console.log(storage);

const host = 'localhost'
const port = 8087

const wss = new WebSocketServer({ host, port });
let local_socket;

console.log("Setting up connection");

const dispatch = {
  'terminate': function(event, ws) {
    console.log("Terminating")

    // It takes a little bit of voodoo to convince the server to
    // terminate.

    // We need to close all open socket connections (of which we have
    // just one), close the listening socket, and terminate the
    // process.
    ws.close();
    wss.close(() => {
      console.log("Server closed");
      process.exit(0);
    });
  },
  'test': function(event) {
    console.log("Test event: ", event.event_number);
  },
  'lock_fields': function(event) {
    console.log("Metadata: ", event);
  },
  'blocklist': function(event, ws) {
    console.log("Sending blocklist");
    ws.send(JSON.stringify({
      status: "blocklist",
      time_limit: "MINUTES",
      action: "DROP"
    }))
  }
}

wss.on('connection', (ws) => {
  console.log("New connection");
  ws.on('message', (data) => {
    // Verify received data
    const j = JSON.parse(data.toString())
    console.log("Dispatching: ", j);
    dispatch[j.event_type](j, ws);
  });
});

const wsl = lo_event.websocketLogger(`ws://${host}:${port}`, storage);

lo_event.init(
  "org.ets.lo_event.test",
  "1",
  [ lo_event.consoleLogger(), wsl ],
  [{'preauth_type': 'test'}],
  [{'postauth_type': 'test'}, util.getBrowserInfo() ],
  lo_event.VERBOSE
)


lo_event.logEvent("test", {"event_number": 1})
lo_event.logEvent("test", {"event_number": 2})
lo_event.logEvent("test", {"event_number": 3})

lo_event.logEvent("blocklist", {"action": "Send us back a block event!"})

lo_event.logEvent("test", {"event_number": 4})
lo_event.logEvent("test", {"event_number": 5})
lo_event.logEvent("terminate", {})

console.log("Done");
