import { WebSocketServer } from 'ws';
import { storage } from '../lo_event/browserStorage.js';
import * as util from '../lo_event/util.js';
import * as debug from '../lo_event/debugLog.js';

import * as loEvent from '../lo_event/lo_event.js';
import * as websocketLogger from '../lo_event/websocketLogger.js';

console.log('Launching server');

console.log(storage);

const host = 'localhost';
const port = 8087;

const wss = new WebSocketServer({ host, port });

console.log('Setting up connection');

const dispatch = {
  terminate: function (event, ws) {
    console.log('Terminating');

    // It takes a little bit of voodoo to convince the server to
    // terminate.

    // We need to close all open socket connections (of which we have
    // just one), close the listening socket, and terminate the
    // process.
    ws.close();
    wss.close(() => {
      console.log('Server closed');
      process.exit(0);
    });
  },
  test: function (event) {
    console.log('Test event: ', event.event_number);
  },
  lock_fields: function (event) {
    console.log('Metadata: ', event);
  },
  blocklist: function (event, ws) {
    console.log('Sending blocklist');
    ws.send(JSON.stringify({
      status: 'blocklist',
      time_limit: 'MINUTES',
      action: 'DROP'
    }));
  },
  debug: function (event) {
    console.log('DEBUG', event);
  }
};

wss.on('connection', (ws) => {
  console.log('New connection');
  ws.on('message', (data) => {
    // Verify received data
    const j = JSON.parse(data.toString());
    console.log('Dispatching: ', j);
    dispatch[j.event_type](j, ws);
  });
});
console.log(wss);

const wsl = websocketLogger.websocketLogger(`ws://${host}:${port}`);

loEvent.init(
  'org.ets.lo_event.test',
  '1',
  [wsl],
  debug.LEVEL.SIMPLE,
  [debug.LOG_OUTPUT.LOGGER(loEvent.logEvent), debug.LOG_OUTPUT.CONSOLE]
);
loEvent.setFieldSet([{ preauth_type: 'test' }]);
loEvent.setFieldSet([{ postauth_type: 'test' }, util.getBrowserInfo()]);
loEvent.go();

loEvent.logEvent('test', { event_number: 1 });
loEvent.logEvent('test', { event_number: 2 });
loEvent.logEvent('test', { event_number: 3 });

// Check the blocklist.
// In this test, we might receive one more event or so.
//
// This takes a second, and the terminate event never comes in, so
// after that the server hangs, so this is behind a flag.
const TEST_BLOCKLIST = false;
if (TEST_BLOCKLIST) {
  loEvent.logEvent('blocklist', { action: 'Send us back a block event!' });
  await new Promise(resolve => setTimeout(resolve, 1000));
}

loEvent.logEvent('test', { event_number: 4 });
loEvent.logEvent('test', { event_number: 5 });
loEvent.logEvent('terminate', {});

console.log('Done');
