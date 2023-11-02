import * as util from '../lo_event/util.js';

let someAsyncCondition = false;
global.document = {};

async function checkCondition () {
  // Example of a condition check
  // Replace this with your actual condition check logic
  console.log('checking', someAsyncCondition);
  return someAsyncCondition;
}

describe('util testing', () => {
  it('Check backoff functionality', async () => {
    // Set the condition to true after some time for demonstration
    setTimeout(() => { someAsyncCondition = true; }, 5000);

    util.backoff(checkCondition, 'Condition not met after retries.')
      .then(() => expect(someAsyncCondition).toBe(true))
      .catch(error => console.error(error.message));
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
