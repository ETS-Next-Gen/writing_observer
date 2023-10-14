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
    default:
      return state;
  }
};

// Create the store
const store = redux.createStore(reducer);
let eventSubscribers = [];

// Action creator function
const emitEvent = (event) => {
  console.log("Emitting event", event);
  return {
    type: 'EMIT_EVENT',
    payload: event
  };
};

const eventQueue = [];
let promise = null;

store.subscribe(() => {
  const state = store.getState();
  if (state.event) {
    console.log('Received event:', state.event);
  }
  if(promise) {
    promise.resolve(state.event);
    promise = null;
  }
  else {
    // This is only useful for awaitEvent below. Otherwise, events build up. Having
    // this event queue may be good or a memory leak. We should figure out whether
    // to have this behind a flag later.
    eventQueue.push(state.event);
  }
  for(i in eventSubscribers) {
    eventSubscribers[i](state.event);
  }
});

store.dispatch(emitEvent('Hello from the server!'));
store.dispatch(emitEvent('Boo!'));

export function reduxLogger(subscribers) {
  if(subscribers != null) {
    eventSubscribers = subscribers;
  }
  emitEvent.lo_name = "Redux Logger";
  emitEvent.lo_id = "redux_logger";
  return (event) => store.dispatch(emitEvent(event));
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
  if(promise) {
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
