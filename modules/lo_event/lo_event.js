/*
  Logging library for Learning Observer clients
*/

// init() has not yet been called. Enqueue events, but don't send them on to
// loggers.
const INIT_FALSE = false;
// init() has been called, but is still waiting on e.g. async metadata
const INIT_INPROGRESS = "init_inprogress";
// init() is done. Note that not all loggers might be ready to send events,
// but they are ready to enqueue events. Most loggers will have
// local queues
const INIT_READY = "init_ready";
let initialized = INIT_FALSE;

// To do: Define and set debug levels
const VERBOSE = 'verbose';
const NONE = 'none';
let debug_log_level = VERBOSE;

// A list of all loggers which should receive events. 
let loggers = [];
// This can either be:
// * dictionaries of metadata
// * functions which return metadata
// * asynchronous functions which return metadata
let metadata = [];
let blocked = false;

export function init(
  source,
  version,
  loggers,
  metadata,
  debug
) {
  initialized = INIT_PROGRESS;
  dequeue();
}

export function log_event(event_type, event) {
}

export function console_logger() {
    /*
      Log to browser JavaScript console
     */
    return console.log;
}

