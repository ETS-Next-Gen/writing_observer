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
import { storage} from './storage.js';

export const EVENT_ACTION = {
  TRANSMIT: 'TRANSMIT',
  MAINTAIN: 'MAINTAIN',
  DROP: 'DROP'
}

/*
 * We make the time limit stochastic, so we don't have all clients
 * retry at the same time if we e.g. block many clients at once.
 */
export const TIME_LIMIT = {
  PERMANENT: -1,
  MINUTES: 60*5*(1+Math.random()), // 5-10 minutes
  DAYS: 60*60*24*(1+Math.random())  // 1-2 days
}

export class BlockError extends Error {
  constructor(message, timeLimit, action) {
    super(message);
    this.message = message;
    this.timeLimit = isNaN(timeLimit) ? TIME_LIMIT[timeLimit] : timeLimit ;
    this.action = EVENT_ACTION[action];  // <-- Check we're in EVENT_ACTION.
  }
}

const action = EVENT_ACTION.TRANSMIT;
const expiration = null;

export function handleBlockError(error) {
  action = error.action;
  if (error.timeLimit === TIME_LIMIT.PERMANENT) {
    expiration = TIME_LIMIT.PERMANENT
  } else {
    time_limit = Date.now() + error.timeLimit;
  }
}

export function storeEvents() {
  return action !== EVENT_ACTION.DROP;
}

export function streamEvents() {
  return action == EVENT_ACTION.TRANSMIT;
}

export function retry() {
  if (expiration === TIME_LIMIT.PERMANENT) {
    return false
  }

  return Date.now() > time_limit;
}
