/*
  Logging library for Learning Observer clients
*/

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
const loggers = []
// This can either be:
// * dictionaries of metadata
// * functions which return metadata
// * asynchronous functions which return metadata
const metadata = []
const blocked = false

// TODO: We should consider specifying a set of verbs, nouns, etc. we
// might use, and outlining what can be expected in the protocol
export function init (
  source,
  version,
  loggers,
  metadata,
  debug_level
) {
  initialized = INIT_INPROGRESS
  dequeue()
}

export function logEvent (eventType, event) {
}

export function consoleLogger () {
  /*
  Log to browser JavaScript console
  */
  return console.log
}
