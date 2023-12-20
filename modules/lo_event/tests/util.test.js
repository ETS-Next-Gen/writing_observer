// TODO:
// * Document
// * More test cases
// * Much better description strings

import * as util from '../lo_event/util.js';

let someAsyncCondition;
global.document = {};

async function checkCondition () {
  // Example of a condition check
  // Replace this with your actual condition check logic
  console.log('Util test: checking', someAsyncCondition);
  return someAsyncCondition;
}

describe('util.js testing', () => {
  describe('Testing Backoff functionality', () => {
    beforeEach(() => {
      console.log('util.js:backoff Setting condition to false');
      someAsyncCondition = false;
    });

    it('Check for generic backoff functionality', async () => {
      console.log('TESTING THIS FUNCTION');
      // Set the condition to true after some time for demonstration
      setTimeout(() => {
        console.log('Util test: setting someAsyncCondition');
        someAsyncCondition = true;
      }, 1000);

      try {
        await util.backoff(checkCondition, 'This should not be seen in the console');
        expect(someAsyncCondition).toBe(true);
      } catch (error) {
        console.error(error.message);
      }
    }, 10000);

    it('Test max retry on backoff', async () => {
      try {
        await util.backoff(
          checkCondition,
          'Condition not met after max retries.',
          [1000, 1000, 1000],
          util.TERMINATION_POLICY.RETRY,
          5
        );
      } catch (error) {
        console.error(error.message);
      }
      expect(someAsyncCondition).toBe(false);
    }, 10000);
  });

  it('Test fullyQualifiedWebsocketURL', () => {
    // We need a function wrapper to check for thrown errors
    expect(function () {
      util.fullyQualifiedWebsocketURL();
    }).toThrow(new Error('Base server is not provided.'));

    global.document.location = 'http://www.example.com';
    expect(util.fullyQualifiedWebsocketURL()).toBe('ws://www.example.com/wsapi/in');
    expect(util.fullyQualifiedWebsocketURL('/ws')).toBe('ws://www.example.com/ws');
    expect(util.fullyQualifiedWebsocketURL('/ws', 'https://learning-observer.org')).toBe('wss://learning-observer.org/ws');
    expect(function () {
      util.fullyQualifiedWebsocketURL('/ws', 'fake://learning-observer.org');
    }).toThrow(new Error('Protocol mapping not found.'));
  });

  it('test deeply merging metadata', async () => {
    const obj1 = { a: 1, b: { c: 3 } };
    const func1 = function () {
      return { b: { d: 4 }, e: 5 };
    };
    expect(await util.mergeMetadata([obj1, func1])).toEqual({ a: 1, b: { c: 3, d: 4 }, e: 5 });
  });
});
