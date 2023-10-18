/*
  Logging library for Learning Observer clients
*/

import { timestampEvent, mergeMetadata } from './util.js';
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
const INIT_LOGGERS_READY = 'init_loggers'; // Loggers ready, but we have not yet sent authenticated or sent metadata
const INIT_ERROR = 'init_error'; // Error occured while initializing data

// We are ready to send events! Note that not all loggers might be
// ready to send events, but some might just queue them up
const INIT_READY = 'init_ready';

let initialized = INIT_FALSE;

// To do: Define and set debug levels
const VERBOSE = 'verbose';
const NONE = 'none';
const debugLogLevel = VERBOSE;

// A list of all loggers which should receive events.
let loggersEnabled = [];
// This can either be:
// * dictionaries of metadata
// * functions which return metadata
// * asynchronous functions which return metadata
let currentState = new Promise((resolve, reject) => { resolve(); });

export { xapi };

const queue = new Queue('LOEvent');

function isInitialized () {
  return initialized === INIT_READY;
}

async function initializeLoggers () {
  console.log('initializing loggers');
  const initializedLoggers = loggersEnabled
    .filter(logger => typeof logger.init === 'function') // Filter out loggers without .init property
    .map(logger => logger.init()); // Call .init() on each logger, which may return a promise

  console.log(initializedLoggers);

  try {
    await Promise.all(initializedLoggers);
    console.log('Loggers initialized!');
    initialized = INIT_LOGGERS_READY;
  } catch (error) {
    initialized = INIT_ERROR;
    console.error('Error resolving logger initializers:', error);
  }
}

export function setFieldSet (data) {
  currentState = currentState.then(
    () => setFieldSetAsync(data)
  );
}

async function setFieldSetAsync (data) {
  const payload = { fields: await mergeMetadata(data), event_type: 'lock_fields' };
  timestampEvent(payload);
  const authpromises = loggersEnabled
    .filter(logger => typeof logger.setField === 'function')
    .map(logger => logger.setField(JSON.stringify(payload)));

  await Promise.all(authpromises);
}

// TODO: We should consider specifying a set of verbs, nouns, etc. we
// might use, and outlining what can be expected in the protocol
export function init (
  source,
  version,
  loggers, // e.g. [console_logger(), websocket_logger("/foo/bar")]
  preauthMetadata, // e.g. [get_chrome_identity, get_local_storage_identity] <-- Just enough to handle server-side opt-outs. E.g. block everyone from a given school
  postauthMetadata, // e.g. [get_browser_info] <-- Enough for debugging and otherwise.
  debugLevel
) {
  // TODO how should use source and version in this context?
  loggersEnabled = loggers;
  initialized = INIT_INPROGRESS;
  currentState = currentState.then(initializeLoggers);
}

export function go () {
  currentState.then(() => {
    initialized = INIT_READY;
    dequeue();
  });
}

async function dequeue () {
  if (!isInitialized()) {
    console.log('failure to dequeue, not initialized');
    return;
  }
  if (!blacklist.streamEvents()) {
    console.log('failure to dequeue, blocked from streaming');
    return;
  }
  if (await queue.count() > 0) {
    try {
      const event = await queue.dequeue();
      const jsonEncodedEvent = JSON.stringify(event);

      for (const logger of loggersEnabled) {
        try {
          logger(jsonEncodedEvent);
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
      await dequeue();
    } catch (error) {
      console.error('Error during dequeue:', error);
    }
  }
}

export function logEvent (eventType, event) {
  // opt out / dead
  if (!blacklist.storeEvents()) {
    return;
  }
  event.event_type = eventType;
  timestampEvent(event);

  queue.enqueue(event);
  dequeue();
}

export function logXAPILite (
  {
    verb,
    object,
    result,
    context,
    attachments
  }
) {
  logEvent(verb,
    { object, result, context, attachments }
  );
}
