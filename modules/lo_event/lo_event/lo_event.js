/*
  Logging library for Learning Observer clients
*/

import { profileInfoWrapper, delay, timestampEvent, fullyQualifiedWebsocketURL, mergeMetadata } from './util.js';
import { Queue } from './queue.js';
import xapi from './xapi.cjs';
import { reduxLogger } from './reduxLogger.js';
import { websocketLogger } from './websocketLogger.js';
import { consoleLogger } from './consoleLogger.js';
import * as blacklist from './blacklist.js';

export { reduxLogger, websocketLogger, consoleLogger };

// Queue events, but don't send them yet.
const INIT_FALSE = false; // init() has not yet been called.
const INIT_INPROGRESS = 'init_inprogress'; // init() has been called, but is still waiting on metadata  
const INIT_METADATA_READY = 'init_metadata'; // Metadata is ready, but we have not yet initialized loggers
const INIT_LOGGERS_READY = 'init_loggers'; // Loggers ready, but we have not yet sent authenticated or sent metadata
const INIT_AUTH_READY = 'init_auth'; // Authenticated, but we have not yet sent metadata
const INIT_ERROR = 'init_error' // Error occured while initializing data

// We are ready to send events! Note that not all loggers might be
// ready to send events, but some might just queue them up
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

const queue = new Queue("MainQueue");
let preauth, postauth;

function loggers_ready() {
  return initialized === INIT_READY;
}

function load_metadata(preauth_metadata, postauth_metadata) {
  return new Promise((resolve, reject) => {
    Promise.all([
      mergeMetadata(preauth_metadata),
      mergeMetadata(postauth_metadata)
      // Add more promises here if needed, perhaps to initialize the loggers
    ])
      .then((results) => {
        console.log("Metadata ready");
        preauth = results[0];
        postauth = results[1];
        initialized = INIT_METADATA_READY;
        resolve();
      })
      .catch((error) => {
        console.error("Metadata error: ", error);
        initialized = INIT_ERROR;
        reject(error);
      });
  });
}

function initialize_loggers() {
  const initializedLoggers = loggersEnabled
    .filter(logger => typeof logger.init === 'function') // Filter out loggers without .init property
    .map(logger => logger.init()); // Call .init() on each logger, which may return a promise

  console.log(initializedLoggers);

  // Wait for all promises to resolve (if any)
  Promise.all(initializedLoggers).then(
    () => { initialized = INIT_LOGGERS_READY; }
  ).catch(error => {
    initialized = INIT_ERROR;
    console.error('Error resolving logger initializers:', error);
  });

  console.log("Loggers initialized!");
}

function sendSetField (data, onSuccess, onFailure) {
  const payload = { ...data, event_type: 'lock_fields' }
  timestampEvent(payload)
  const authpromises = loggersEnabled
    .filter(logger => typeof logger.setField === 'function')
    .map(logger => logger.setField(JSON.stringify(payload)))

  Promise.all(authpromises).then(
    () => { if (onSuccess) onSuccess() }
  ).catch(error => {
    if (onFailure) onFailure()
    console.error('Auth error:', error)
  });
}

function send_preauth() {
  const authpromises = loggersEnabled
    .filter(logger => typeof logger.preauth === 'function')
    .map(logger => logger.preauth(preauth));

  Promise.all(authpromises).then(
    () => { initialized = INIT_AUTH_READY; }
  ).catch(error => {
    initialized = INIT_ERROR;
    // TODO: Handle opt outs here
    console.error('Auth error:', error);
  });
}

function send_postauth() {
  const metadatapromises = loggersEnabled
    .filter(logger => typeof logger.postauth === 'function')
    .map(logger => logger.postauth(postauth));

  Promise.all(metadatapromises).then(
    () => { initialized = INIT_READY; }
  ).catch(error => {
    initialized = INIT_ERROR;
    // TODO: Handle opt outs here
    console.error('Auth error:', error);
  });
}

// TODO: We should consider specifying a set of verbs, nouns, etc. we
// might use, and outlining what can be expected in the protocol
export function init(
  source,
  version,
  loggers, // e.g. [console_logger(), websocket_logger("/foo/bar")]
  preauthMetadata, // e.g. [get_chrome_identity, get_local_storage_identity] <-- Just enough to handle server-side opt-outs. E.g. block everyone from a given school
  postauthMetadata, // e.g. [get_browser_info] <-- Enough for debugging and otherwise.
  debugLevel
) {
  preauthMetadata.push({ source, version })
  console.log(preauthMetadata);
  loggersEnabled = loggers;
  initialized = INIT_INPROGRESS;
  load_metadata(preauthMetadata, postauthMetadata)
    .then(initialize_loggers)
    .then(res => sendSetField(preauth, () => { initialized = INIT_AUTH_READY; }, () => { initialized = INIT_ERROR; }))
    .then(res => sendSetField(postauth, () => { initialized = INIT_READY; }, () => { initialized = INIT_ERROR; }))
}

export function logEvent(eventType, event) {
  // opt out / dead
  if (!blacklist.storeEvents()) {
    return;
  }

  event.event_type = eventType;
  timestampEvent(event);
  const jsonEncodedEvent = JSON.stringify(event);

  // To do: Pass these through a queue
  if (!blacklist.streamEvents()) {
    return;
  }

  for (let i = 0; i < loggersEnabled.length; i++) {
    try {
      loggersEnabled[i](jsonEncodedEvent);
    } catch (error) {
      if (error instanceof blacklist.BlockError) {
        // Handle BlockError exception here
        blacklist.handleBlockError(error);
      } else {
        // Other types of exceptions will propagate up
        throw error;
      }
    }
  }
}

export function logXAPILite(
  { verb,
    object,
    result,
    context,
    attachments }
) {
  logEvent(verb,
    { object, result, context, attachments }
  );
}

// const url = fullyQualifiedWebsocketURL('/ws', 'http://127.0.0.1:8765')
// const log = websocketLogger(url, storage)
// log('test')
// log('123')
