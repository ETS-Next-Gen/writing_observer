/*
  Logging library for Learning Observer clients
*/

import { timestampEvent, mergeMetadata } from './util.js';
import * as Queue from './queue.js';
import * as disabler from './disabler.js';
import * as debug from './debugLog.js';

export const QueueType = Queue.QueueType;

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

// promise pipeline to ensure we handle all initialization
// and metadata before routing events to their loggers
let currentState = new Promise((resolve, reject) => { resolve(); });

let queue;

function isInitialized () {
  return initialized === INIT_READY;
}

/**
 * Collect all enabled loggers with an init function, call it,
 * and wait for all of them to finish initializing. We add this
 * function to our `currentState` pipeline to ensure loggers
 * are ready to go before we send events.
 */
async function initializeLoggers () {
  debug.info('initializing loggers');
  const initializedLoggers = loggersEnabled
    .filter(logger => typeof logger.init === 'function') // Filter out loggers without .init property
    .map(logger => logger.init()); // Call .init() on each logger, which may return a promise

  try {
    await Promise.all(initializedLoggers);
    debug.info('Loggers initialized!');
    initialized = INIT_LOGGERS_READY;
  } catch (error) {
    initialized = INIT_ERROR;
    debug.error('Error resolving logger initializers:', error);
  }
}

/**
 * Set specific key/value pairs using the `lock_fields`
 * event. We use this to set specific fields that we want
 * included overall for subsequent events to prevent
 * sending the same information in each event.
 *
 * This is useful for items such as `source` and `version`
 * which should be the same for every event.
 *
 * Note that at the time this was written, we did not consider the use
 * case of using setFieldSet after INIT_READY. This may or may not
 * work, but has complex issues with consistency and async (e.g. if
 * setFieldSet executes after a send event) and especially with
 * disconnects (e.g. will the field set be configured for the right
 * events). At some point, this should probably be made into a queued
 * event, and reconnection issues should be figured out.
 */
export function setFieldSet (data) {
  currentState = currentState.then(
    () => setFieldSetAsync(data)
  );
}



/**
 * Runs and awaits for all loggers to run their `setField` command
 */
async function setFieldSetAsync (data) {
  const payload = { fields: await mergeMetadata(data), event: 'lock_fields' };
  timestampEvent(payload);
  const authpromises = loggersEnabled
    .filter(logger => typeof logger.setField === 'function')
    .map(logger => logger.setField(JSON.stringify(payload)));

  await Promise.all(authpromises);
}

// TODO: We should consider specifying a set of verbs, nouns, etc. we
// might use, and outlining what can be expected in the protocol
// TODO: We should consider structing / destructing here
export function init (
  source,
  version,
  loggers, // e.g. [console_logger(), websocket_logger("/foo/bar")]
  {
    debugLevel = debug.LEVEL.SIMPLE,
    debugDest = [debug.LOG_OUTPUT.CONSOLE],
    useDisabler = true,
    queueType = Queue.QueueType.AUTODETECT
  } = {}
) {
  queue = new Queue.Queue('LOEvent', { queueType } );

  if (source === null || typeof source !== 'string') {
    throw new Error('source must be a non-null string');
  }
  if (version === null || typeof version !== 'string') {
    throw new Error('version must be a non-null string');
  }
  debug.setLevel(debugLevel);
  debug.setLogOutputs(debugDest);
  if (useDisabler) {
    currentState = currentState.then(() => disabler.init(useDisabler));
  }

  loggersEnabled = loggers;
  initialized = INIT_INPROGRESS;
  currentState = currentState.then(initializeLoggers).then(
    () => setFieldSet([{ source, version }]));
}

export function go () {
  currentState.then(() => {
    initialized = INIT_READY;
    queue.startDequeueLoop({
      initialize: isInitialized,
      shouldDequeue: disabler.retry,
      onDequeue: sendEvent
    });
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

export function logEvent (eventType, event) {
  // opt out / dead
  if (!disabler.storeEvents()) {
    return;
  }
  event.event = eventType;
  timestampEvent(event);

  queue.enqueue(event);
}

/**
 * We would like to be able to log events roughly following the xAPI
 * conventions (and possibly Caliper conventions). This allows us to
 * explicitly structure events with the same fields as xAPI, and
 * might have validation logic in the future. However, we have not
 * figured out the best way to do this, so please treath this as
 * stub / in-progress code.
 *
 * In the long term, we'd like to be as close to standards as possible.
 */
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
