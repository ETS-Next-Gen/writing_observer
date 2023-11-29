/*
 * Code to handle blacklists, opt-ins, opt-outs, etc.
 *
 * Unfinished. We need to flush out storage.js and connect to make
 * this work.
 */

/*
 * We have different types of opt-in/opt-out scenarios. For example:
 * - If we have a contractual gap with a school, we might want to hold
 *   events on the client-side pending resolution
 * - If a school or student does not want us to collect their data, but
 *   have the extension installed, we don't want to store them
 *   client-side.
 */
import { storage } from './browserStorage.js';
import * as debug from './debugLog.js';
import * as util from './util.js';

export const EVENT_ACTION = {
  TRANSMIT: 'TRANSMIT',
  MAINTAIN: 'MAINTAIN',
  DROP: 'DROP'
};

/*
 * We make the time limit stochastic, so we don't have all clients
 * retry at the same time if we e.g. block many clients at once.
 */
export const TIME_LIMIT = {
  PERMANENT: -1,
  MINUTES: 1000 * 60 * 5 * (1 + Math.random()), // 5-10 minutes
  DAYS: 1000 * 60 * 60 * 24 * (1 + Math.random()) // 1-2 days
};

const DISABLER_STORE = 'disablerState';

export class BlockError extends Error {
  constructor (message, timeLimit, action) {
    super(message);
    this.name = 'BlockError';
    this.message = message;
    this.timeLimit = isNaN(timeLimit) ? TIME_LIMIT[timeLimit] : timeLimit;
    this.action = EVENT_ACTION[action]; // <-- Check we're in EVENT_ACTION.
  }
}

const DEFAULTS = {
  action: EVENT_ACTION.TRANSMIT,
  expiration: null
};

let { action, expiration } = DEFAULTS;

export async function init (defaults = null) {
  defaults = defaults || DEFAULTS;

  return new Promise((resolve, reject) => {
    // Check if storage is defined
    if (!storage || !storage.get) {
      debug.error('Storage is not set or storage.get is undefined. This should never happen.');
      reject(new Error('Storage or storage.get is undefined'));
    } else {
      // Fetch initial values from storage upon loading
      storage.get(DISABLER_STORE, (storedState) => {
        storedState = storedState[DISABLER_STORE] || {};
        action = storedState.action || DEFAULTS.action;
        expiration = storedState.expiration || DEFAULTS.expiration;
        debug.info(`Initialized disabler. action: ${action} expiration: ${new Date(expiration).toString()}`);
        resolve();
      });
    }
  });
}

export function handleBlockError (error) {
  action = error.action;
  if (error.timeLimit === TIME_LIMIT.PERMANENT) {
    expiration = TIME_LIMIT.PERMANENT;
  } else {
    expiration = Date.now() + error.timeLimit;
  }
  storage.set({ [DISABLER_STORE]: { action, expiration } });
}

export function storeEvents () {
  return action !== EVENT_ACTION.DROP;
}

export function streamEvents () {
  return action === EVENT_ACTION.TRANSMIT;
}

export async function retry () {
  if (expiration === TIME_LIMIT.PERMANENT) {
    return false;
  }
  const now = Date.now();
  if (now < expiration) {
    debug.info(`waiting for expiration to happen ${new Date(expiration).toString()}`);
    await util.delay(expiration - now);
    debug.info('we are done waiting');
  }
  action = DEFAULTS.action;
  expiration = DEFAULTS.expiration;
  storage.set({ [DISABLER_STORE]: { action, expiration } });
  return true;
}
