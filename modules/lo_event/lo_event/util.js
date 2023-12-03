import * as crypto from 'crypto';
import { storage } from './browserStorage.js';

/*
  Browser information object, primarily for debugging. Note that not
  all fields will be available in all browsers and contexts. If not
  available, it will return null (this is even usable in node.js,
  but it will simply return that there is no navigator, window, or
  document object).

  @returns {Object} An object containing the browser's navigator, window, and document information.

  Example usage:
    const browserInfo = getBrowserInfo();
    console.log(browserInfo);

  TODO: This code is a little bit repetitive. Can we apply DRY somehow?
*/
export function getBrowserInfo () {
  const fields = [
    'appCodeName',
    'appName',
    'buildID',
    'cookieEnabled',
    'deviceMemory',
    'language',
    'languages',
    'onLine',
    'oscpu',
    'platform',
    'product',
    'productSub',
    'userAgent',
    'webdriver'
  ];

  const connectionFields = [
    'effectiveType',
    'rtt',
    'downlink',
    'type',
    'downlinkMax'
  ];

  const documentFields = [
    'URL',
    'baseURI',
    'characterSet',
    'charset',
    'compatMode',
    'cookie',
    'currentScript',
    'designMode',
    'dir',
    'doctype',
    'documentURI',
    'domain',
    'fullscreen',
    'fullscreenEnabled',
    'hidden',
    'inputEncoding',
    'isConnected',
    'lastModified',
    'location',
    'mozSyntheticDocument',
    'pictureInPictureEnabled',
    'plugins',
    'readyState',
    'referrer',
    'title',
    'visibilityState'
  ];

  const windowFields = [
    'closed',
    'defaultStatus',
    'innerHeight',
    'innerWidth',
    'name',
    'outerHeight',
    'outerWidth',
    'pageXOffset',
    'pageYOffset',
    'screenX',
    'screenY',
    'status'
  ];

  const browserInfo = {};

  if (typeof navigator === 'undefined') {
    browserInfo.navigator = null;
  } else {
    for (let i = 0; i < fields.length; i++) {
      browserInfo[fields[i]] = navigator[fields[i]];
    }

    browserInfo.connection = {};
    if (navigator.connection) {
      for (let i = 0; i < connectionFields.length; i++) {
        browserInfo.connection[connectionFields[i]] = navigator.connection[connectionFields[i]];
      }
    }
  }

  if (typeof document === 'undefined') {
    browserInfo.document = null;
  } else {
    browserInfo.document = {};
    for (let i = 0; i < documentFields.length; i++) {
      browserInfo.document[documentFields[i]] = document[documentFields[i]];
    }
  }

  if (typeof window === 'undefined') {
    browserInfo.window = null;
  } else {
    browserInfo.window = {};
    for (let i = 0; i < windowFields.length; i++) {
      browserInfo.window[windowFields[i]] = window[windowFields[i]];
    }
  }

  return { browser_info: browserInfo };
}

/*
  This function is a wrapper for retrieving profile information using
  the Chrome browser's identity API. It addresses a bug in the Chrome
  function and converts it into a modern async function. The bug it
  works around can be found at
  https://bugs.chromium.org/p/chromium/issues/detail?id=907425#c6.

  To do: Add chrome.identity.getAuthToken() to retrieve an
  authentication token, so we can do real authentication.

  Returns:
    A Promise that resolves with the user's profile information.

  Example usage:
    const profileInfo = await profileInfoWrapper();
    console.log(profileInfo);
  */
export function profileInfoWrapper () {
  if (typeof chrome !== 'undefined' && chrome.identity) {
    try {
      return new Promise((resolve, reject) => {
        chrome.identity.getProfileUserInfo({ accountStatus: 'ANY' }, function (data) {
          resolve(data);
        });
      });
    } catch (e) {
      return new Promise((resolve, reject) => {
        chrome.identity.getProfileUserInfo(function (data) {
          resolve(data);
        });
      });
    }
  }
  // Default to an empty object
  return new Promise((resolve, reject) => {
    resolve({});
  });
}

/*
  Generate a unique key, which can be used for session IDs, anonymous user IDs, and other similar purposes.

  Parameters:
  - prefix (str): Optional prefix to prepend to the generated key.

  Returns:
  str: A string representing the unique key, in the format "{prefix}-{randomUUID}-{timestamp}". If no prefix is provided, the format will be "{randomUUID}-{timestamp}".
  */
export function keystamp (prefix) {
  return `${prefix ? prefix + '-' : ''}${crypto.randomUUID()}-${Date.now()}`;
}

/*
  Create a fully-qualified web socket URL.

  All parameters are optional when running on a web page. On an extension,
  we need, at least, the base server.

  This will:
  * Convert relative URLs into fully-qualified ones, if necessary
  * Convert HTTP/HTTPS URLs into WS/WSS ones, if necessary

  Example usage:
    const serverURL = fullyQualifiedWebsocketURL('/websocket/endpoint', 'http://websocket.server');
    websocketConnection(serverURL);

  # TODO: Give actual examples of input / output in example
  */
export function fullyQualifiedWebsocketURL (defaultRelativeUrl, defaultBaseServer) {
  const relativeUrl = defaultRelativeUrl || '/wsapi/in';
  const baseServer = defaultBaseServer || (typeof document !== 'undefined' && document.location);

  if (!baseServer) {
    throw new Error('Base server is not provided.');
  }

  const url = new URL(relativeUrl, baseServer);

  const protocolMap = { 'https:': 'wss:', 'http:': 'ws:', 'ws:': 'ws:', 'wss:': 'wss' };

  if (!protocolMap[url.protocol]) {
    throw new Error('Protocol mapping not found.');
  }

  url.protocol = protocolMap[url.protocol];

  return url.href;
}

/**
 * Example usage:
 *  event = { event: 'ADD', data: 'stuff' }
 *  timestampEvent(event)
 *  event
 *  // { event: 'ADD', data: 'stuff', metadata: { ts, human_ts, iso_ts } }
 */
export function timestampEvent (event) {
  if (!event.metadata) {
    event.metadata = {};
  }

  event.metadata.ts = Date.now();
  event.metadata.human_ts = Date();
  event.metadata.iso_ts = new Date().toISOString();
}

/**
 * We provide an id for each system that is stored
 * locally with the client. This allows us to more easily
 * parse events when debugging in specific contexts.
 *
 * Example usage:
 *  const debugMetadata = await debuggingMetadata();
 *  console.log(debugMetadata);
 *
 * TODO: Better function name. ID is for debugging, but it's not clear
 * what it is from the name
 */
export function debuggingMetadata () {
  return new Promise((resolve, reject) => {
    const metadata = {};

    storage.get(['logger_id', 'name'], (result) => {
      if (result.logger_id) {
        metadata.logger_id = result.logger_id;
      } else {
        metadata.logger_id = keystamp('lid');
        storage.set({ logger_id: metadata.logger_id });
      }
      if (result.name) {
        metadata.name = result.name;
      }
      resolve(metadata);
    });
  });
}

/**
 * Deeply merge `source` into `target`.
 * `target` should be passed by reference
 *
 * This is a helper function for `mergeMetadata`.
 *
 * Example usage:
 *  const obj1 = { a: 1, b: { c: 3 } };
 *  const obj2 = { b: { d: 4 }, e: 5 };
 *  util.mergeDictionary(obj1, obj2);
 *  obj1
 *  // { a: 1, b: { c: 3, d: 4 }, e: 5 }
 */
function mergeDictionary (target, source) {
  for (const key in source) {
    if (Object.prototype.hasOwnProperty.call(target, key)) {
      mergeDictionary(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
}

/**
 * Merges the output of dictionaries, sync functions, and async
 * functions into a single master dictionary.
 *
 * Functions and async functions should return dictionaries.
 *
 * @param {Array} inputList - List of dictionaries, sync functions, and async functions
 * @returns {Promise<Object>} - A Promise that resolves to the compiled master dictionary
 *
 * Example usage:
 *  const metadata = await mergeMetadata([ browserInfo(), { source: '0.0.1' }, extraMetadata() ])
 *  console.log(metadata);
 * // { browserInfo: {}, source: '0.0.1', metadata: { extra: 'extra data' }}
 */
export async function mergeMetadata (inputList) {
  // Initialize the master dictionary
  const masterDict = {};

  // Iterate over each item in the input list
  for (const item of inputList) {
    let result;

    if (typeof item === 'object') {
      // If the item is a dictionary, merge it into the master dictionary
      mergeDictionary(masterDict, item);
    } else if (typeof item === 'function') {
      // If the item is a function (sync or async), execute it
      result = await item();

      if (typeof result === 'object') {
        // If the result of the function is a dictionary, merge it into the master dictionary
        mergeDictionary(masterDict, result);
      } else {
        console.log('Ignoring non-dictionary result:', result);
      }
    } else {
      console.log('Ignoring invalid item:', item);
    }
  }

  return masterDict;
}

export function delay (ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
const MS = 1;
const SECS = 1000 * MS;
const MINS = 60 * SECS;
const HOURS = 60 * MINS;

/**
 * This function repeatedly tries to run another function
 * until it returns a truthy value while waiting a set amount
 * of time inbetween each attempt.
 *
 * Example usage:
 *  util.backoff(checkCondition, 'Condition not met after retries.')
 *    .then(() => console.log('Condition met.'))
 *    .catch(error => console.error(error.message));
 *
 * TODO we ought to allow different termination conditions
 * e.g. die vs continue retrying with last delay amount
 *
 * @param {*} predicate function that returns truthy value
 * @param {*} errorMessage message to be thrown when we run out of delays
 * @param {*} delays list of MS values to be await in order
 * @default delays defaults to [100ms, 1sec, 1min, 5min, 30min]
 * @returns returns when predicate is true or throws errorMessage
 */
export async function backoff (
  predicate,
  errorMessage = 'Could not resolve backoff function',
  // In milliseconds, time between retries until we fail.
  delays = [100 * MS, 1 * SECS, 10 * SECS, 1 * MINS, 5 * MINS, 30 * MINS]
) {
  for (let i = 0; i < delays.length; i++) {
    if (await predicate()) {
      return true;
    }
    await delay(delays[i]);
  }
  throw new Error(errorMessage);
}

// The `once` function is a decorater function that takes in a
// function `func` and returns a new function. The returned function
// can only be called once, and any subsequent calls will result in an
// error. It is intended for the event loops in the various queue
// code.
//
// This is similar to the underscore once, but in contrast to that
// one, subsequent calls give an error rather than silently doing
// nothing. This is important as we are debugging the code. In the
// future, we might make this configurable or just switch, but for
// now, we'd like to understand if this ever happens and make it very
// obvious,
export function once (func) {
  const run = false;
  return function () {
    if (!run) {
      return func.apply(this, arguments);
    } else {
      console.log('>>>> Function called more than once. This should never happen <<<<');
      throw new Error('Error! Function was called more than once! This should never happen');
    }
  };
}
