import * as lo_event from '../lo_event/lo_event.js'
import * as reduxLogger from '../lo_event/reduxLogger.js'
import * as util from '../lo_event/util.js'

const rl = lo_event.reduxLogger();

console.log("Initializing lo_event")
lo_event.init(
  "org.ets.lo_event.test",
  "1",
  [ lo_event.consoleLogger(), rl ],
  [{'preauth_type': 'test'}],
  [{'postauth_type': 'test'}, util.getBrowserInfo() ],
  lo_event.VERBOSE
)
console.log("Initialized");
lo_event.logEvent("test", {"event_number": 1})
lo_event.logEvent("test", {"event_number": 2})
lo_event.logEvent("test", {"event_number": 3})

console.log("Preparing to run test cases");

describe('lo_event testing', () => {
  it('Check basic event handling', async () => {
    console.log("Running test cases");
    // Are events coming in in the right order?
    expect((await reduxLogger.awaitEvent()).event_number).toBe(1);
    expect((await reduxLogger.awaitEvent()).event_number).toBe(2);
    console.log("Test Event 3: ", reduxLogger.awaitEvent()); // <- event number 3
    // Are metadata being sent?
    expect(rl.get_preauth().preauth_type).toBe('test');
    expect(rl.get_postauth().postauth_type).toBe('test');
  });
})

