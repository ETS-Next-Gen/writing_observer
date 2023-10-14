import * as lo_event from '../lo_event/lo_event.js'
import * as reduxLogger from '../lo_event/reduxLogger.js'

console.log("Initializing lo_event")
lo_event.init(
  "org.ets.lo_event.test",
  "1",
  [ lo_event.consoleLogger(), lo_event.reduxLogger() ],
  [],
  [],
  lo_event.VERBOSE
)

lo_event.logEvent("test", {})
console.log("Incoming event:", await reduxLogger.awaitEvent())
console.log("Incoming event:", await reduxLogger.awaitEvent())
