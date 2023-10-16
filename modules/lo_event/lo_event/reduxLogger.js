/*
 * This is a logger which uses redux in order to route events to one
 * or more subscribers. It is currently used for working with the test
 * framework. In the future, it may be used more broadly.
 */

import redux from 'redux';

// Reducer function
const reducer = (state = {}, action) => {
  switch (action.type) {
    case 'EMIT_EVENT':
      return { ...state, event: action.payload };
    case 'EMIT_PREAUTH':
      return { ...state, preauth: action.payload };
    case 'EMIT_POSTAUTH':
      return { ...state, postauth: action.payload };
    default:
      return state;
  }
};

// Create the store
const store = redux.createStore(reducer);
let eventSubscribers = [];

// Action creator function
const emitEvent = (event) => {
  return {
    type: 'EMIT_EVENT',
    payload: event
  };
};

// Action creator function
const emitPreauth = (preauth) => {
  return {
    type: 'EMIT_PREAUTH',
    payload: preauth
  };
};

// Action creator function
const emitPostauth = (postauth) => {
  return {
    type: 'EMIT_POSTAUTH',
    payload: postauth
  };
};

const eventQueue = [];
let promise = null;

let previousEvent = null;

let preauth = null;
let postauth = 5;

store.subscribe(() => {
  const state = store.getState();
  if (state.event) {
    console.log('Received event:', state.event);
  }
  preauth = state.preauth;
  postauth = state.postauth;
  console.log('state', state);
  const event = JSON.parse(state.event);
  console.log(event);
  if (event === previousEvent) {
    return;
  }
  previousEvent = event;

  if (promise) {
    promise.resolve(event);
    promise = null;
  } else {
    // This is only useful for awaitEvent below. Otherwise, events build up. Having
    // this event queue may be good or a memory leak. We should figure out whether
    // to have this behind a flag later.
    eventQueue.push(event);
  }
  for (const i in eventSubscribers) {
    eventSubscribers[i](event);
  }
})

export function reduxLogger (subscribers) {
  if (subscribers != null) {
    eventSubscribers = subscribers;
  }
  emitEvent.lo_name = 'Redux Logger';
  emitEvent.lo_id = 'redux_logger';

  function logEvent (event) {
    store.dispatch(emitEvent(event))
  }

  logEvent.get_preauth = function () { return preauth };
  logEvent.get_postauth = function () { return postauth };

  logEvent.preauth = function (preauth) {
    store.dispatch(emitPreauth(preauth));
  }

  logEvent.postauth = function (postauth) {
    store.dispatch(emitPostauth(postauth));
  }

  logEvent.setField = function (event) {
    console.log(event);
    store.dispatch(emitEvent(event));
  }

  return logEvent;
}

// This is a convenience function which lets us simply await events.
//
// Note that this should not be used in threaded code or in multiple
// places at the same time in async code. It's a convenience function
// for _simple_ code.
export const awaitEvent = () => {
  if (eventQueue.length > 0) {
    return eventQueue.shift(); // Return the first event in the queue
  }
  if (promise) {
    throw new Error('Only one call to awaitEvent is allowed at a time');
  }

  // Create a new promise
  let resolvePromise;

  promise = new Promise((resolve) => {
    resolvePromise = resolve;
  });

  promise.resolve = resolvePromise;
  return promise;
}
