/*
  Logging library for Learning Observer clients
*/

import { profileInfoWrapper, delay, defaultEventMetadata, fullyQualifiedWebsocketURL } from './util.js';
import { Queue } from './queue.js';
import xapi from './xapi.cjs';
import { reduxLogger } from './reduxLogger.js';
import { websocketLogger } from './websocketLogger.js';
import { consoleLogger } from './consoleLogger.js';
export { reduxLogger, websocketLogger, consoleLogger };

// init() has not yet been called. Enqueue events, but don't send them on to
// loggers.
const INIT_FALSE = false
// init() has been called, but is still waiting on e.g. async metadata
const INIT_INPROGRESS = 'init_inprogress'
// init() is done. Note that not all loggers might be ready to send events,
// but they are ready to enqueue events. Most loggers will have
// local queues
const INIT_READY = 'init_ready'
let initialized = INIT_FALSE

// To do: Define and set debug levels
const VERBOSE = 'verbose'
const NONE = 'none'
const debugLogLevel = VERBOSE

// A list of all loggers which should receive events.
let loggersEnabled = []
// This can either be:
// * dictionaries of metadata
// * functions which return metadata
// * asynchronous functions which return metadata
const metadata = []
const blocked = false

export { xapi }

// TODO: We should consider specifying a set of verbs, nouns, etc. we
// might use, and outlining what can be expected in the protocol
export function init (
  source,
  version,
  loggers,   // e.g. [console_logger(), websocket_logger("/foo/bar")]
  preauth_metadata, // e.g. [get_chrome_identity, get_local_storage_identity] <-- Just enough to handle server-side opt-outs. E.g. block everyone from a given school
  postauth_metadata, // e.g. [get_browser_info] <-- Enough for debugging and otherwise.
  debugLevel
) {
  initialized = INIT_INPROGRESS;
  // TODO handle rest of initialization
  loggersEnabled = loggers;
}

export function logEvent (eventType, event) {
  event.event_type = eventType;

  if (event.wa_source === null) {
    event.wa_source = 'background_page';
  }
  const jsonEncodedEvent = JSON.stringify(event);
  for (let i = 0; i < loggersEnabled.length; i++) {
    loggersEnabled[i](jsonEncodedEvent);
  }
}

// storage mirrors the capability of `chrome.storage.sync`
// this is used for testing purposes
const storage = {
  data: {},
  set: function (items, callback) {
    this.data = { ...this.data, ...items };
    if (callback) callback();
  },
  get: function (keys, callback) {
    let result = {};
    if (Array.isArray(keys)) {
      keys.forEach(key => {
        if (this.data.hasOwnProperty(key)) {
          result[key] = this.data[key];
        }
      })
    } else if (typeof keys === 'string') {
      if (this.data.hasOwnProperty(keys)) {
        result[keys] = this.data[keys];
      }
    } else {
      result = { ...this.data };
    }
    if (callback) callback(result);
  }
}

// const url = fullyQualifiedWebsocketURL('/ws', 'http://127.0.0.1:8765')
// const log = websocketLogger(url, storage)
// log('test')
// log('123')
