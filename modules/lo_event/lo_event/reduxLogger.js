/*
 * This is a logger which uses redux in order to route events to one
 * or more subscribers. It is currently used for working with the test
 * framework. In the future, it may be used more broadly.
 */

import redux from 'redux';

// Action creator function
const emitEvent = (event) => {
  return {
    type: 'EMIT_EVENT',
    payload: event
  };
};

// Action creator function
const emitSetField = (setField) => {
  return {
    type: 'EMIT_LOCKFIELDS',
    payload: setField
  };
};

const eventQueue = [];
let store;
let promise = null;
let previousEvent = null;
let lockFields = null;
let eventSubscribers = [];

function initializeStore () {
  // Reducer function
  const reducer = (state = {}, action) => {
    let payload;
    switch (action.type) {
      case 'EMIT_EVENT':
        return { ...state, event: action.payload };
      case 'EMIT_LOCKFIELDS':
        payload = JSON.parse(action.payload);
        return {
          ...state,
          lock_fields: {
            ...payload,
            fields: {
              ...(state.lock_fields ? state.lock_fields.fields : {}),
              ...payload.fields
            }
          }
        };

      default:
        return state;
    }
  };

  // Create the store
  store = redux.createStore(reducer);

  store.subscribe(() => {
    const state = store.getState();
    if (state.lock_fields) {
      lockFields = state.lock_fields.fields;
    }
    if (!state.event) return;
    console.log('Received event:', state.event);
    const event = JSON.parse(state.event);
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
  });
}

export function reduxLogger (subscribers) {
  if (subscribers != null) {
    eventSubscribers = subscribers;
  }

  function logEvent (event) {
    store.dispatch(emitEvent(event));
  }
  logEvent.lo_name = 'Redux Logger';
  logEvent.lo_id = 'redux_logger';

  logEvent.init = async function () {
    initializeStore();
  };

  logEvent.setField = function (event) {
    store.dispatch(emitSetField(event));
  };

  logEvent.getLockFields = function () { return lockFields; };

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
};
