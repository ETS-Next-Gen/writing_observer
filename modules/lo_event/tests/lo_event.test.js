import * as loEvent from '../lo_event/lo_event.js';
import * as reduxLogger from '../lo_event/reduxLogger.js';
import * as util from '../lo_event/util.js';

const rl = loEvent.reduxLogger();

console.log('Initializing loEvent');
loEvent.init(
  'org.ets.lo_event.test',
  '1',
  [loEvent.consoleLogger(), rl],
  loEvent.VERBOSE
);
loEvent.setFieldSet([{ preauth_type: 'test' }]);
loEvent.setFieldSet([{ postauth_type: 'test' }, util.getBrowserInfo()]);
loEvent.go();

console.log('Initialized');
loEvent.logEvent('test', { event_number: 1 });
loEvent.logEvent('test', { event_number: 2 });
loEvent.logEvent('test', { event_number: 3 });

console.log('Preparing to run test cases');

describe('loEvent testing', () => {
  it('Check basic event handling', async () => {
    console.log('Running test cases');
    // Are events coming in in the right order?
    expect((await reduxLogger.awaitEvent()).event_number).toBe(1);
    expect((await reduxLogger.awaitEvent()).event_number).toBe(2);
    console.log('Test Event 3: ', reduxLogger.awaitEvent()); // <- event number 3
    // Are metadata being sent?
    console.log('redux lock fields', rl.getLockFields());
  });
});
