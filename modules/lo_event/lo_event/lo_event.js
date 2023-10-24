/*
  Logging library for Learning Observer clients
*/

import { timestampEvent, mergeMetadata } from './util.js';
import { Queue } from './queue.js';
import * as disabler from './disabler.js';
import * as debug from './debugLog.js';

// Queue events, but don't send them yet.
const INIT_FALSE = false; // init() has not yet been called.
const INIT_INPROGRESS = 'init_inprogress'; // init() has been called, but is still waiting on metadata
const INIT_LOGGERS_READY = 'init_loggers'; // Loggers ready, but we have not yet sent authenticated or sent metadata
const INIT_ERROR = 'init_error'; // Error occured while initializing data

// We are ready to send events! Note that not all loggers might be
// ready to send events, but some might just queue them up
const INIT_READY = 'init_ready';

let initialized = INIT_FALSE;

// A list of all loggers which should receive events.
let loggersEnabled = [];
// This can either be:
// * dictionaries of metadata
// * functions which return metadata
// * asynchronous functions which return metadata
let currentState = new Promise((resolve, reject) => { resolve(); });

const queue = new Queue('LOEvent');

function isInitialized () {
  return initialized === INIT_READY;
}

async function initializeLoggers () {
  debug.log('initializing loggers');
  const initializedLoggers = loggersEnabled
    .filter(logger => typeof logger.init === 'function') // Filter out loggers without .init property
    .map(logger => logger.init()); // Call .init() on each logger, which may return a promise

  debug.log(initializedLoggers);

  try {
    await Promise.all(initializedLoggers);
    debug.log('Loggers initialized!');
    initialized = INIT_LOGGERS_READY;
  } catch (error) {
    initialized = INIT_ERROR;
    debug.log('Error resolving logger initializers:', error);
  }
  return Promise.all(initializedLoggers);
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
  debugLevel = debug.LEVEL.SIMPLE,
  debugDest = [debug.DESTINATIONS.CONSOLE]
) {
  if (source === null || typeof source !== 'string') {
    throw new Error('source must be a non-null string');
  }
  if (version === null || typeof version !== 'string') {
    throw new Error('version must be a non-null string');
  }
  debug.setLevel(debugLevel);
  debug.setDestinations(debugDest);

  loggersEnabled = loggers;
  initialized = INIT_INPROGRESS;
  currentState = currentState.then(initializeLoggers).then(
    () => setFieldSet([{ source, version }]));
}

export function go () {
  currentState.then(() => {
    initialized = INIT_READY;
    dequeue();
  });
}

function sendEvent (event) {
  const jsonEncodedEvent = JSON.stringify(event);
  for (const logger of loggersEnabled) {
    try {
      logger(jsonEncodedEvent);
    } catch (error) {
      if (error instanceof disabler.BlockError) {
        // Handle BlockError exception here
        disabler.handleBlockError(error);
      } else {
        // Other types of exceptions will propagate up
        throw error;
      }
    }
  }
}

async function dequeue () {
  if (!isInitialized()) {
    debug.log('failure to dequeue, not initialized');
    return;
  }
  if (!disabler.streamEvents()) {
    debug.log('failure to dequeue, blocked from streaming');
    return;
  }
  while (true) {
    try {
      const event = await queue.nextItem();
      sendEvent(event);
    } catch (error) {
      debug.log('Error during dequeue or sending of event:', error);
    }
  }
}

export function logEvent (eventType, event) {
  // opt out / dead
  if (!disabler.storeEvents()) {
    return;
  }
  event.event_type = eventType;
  timestampEvent(event);

  queue.enqueue(event);
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
