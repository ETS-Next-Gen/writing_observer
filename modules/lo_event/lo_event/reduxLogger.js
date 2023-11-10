/*
 * This is a logger which uses redux in order to route events to one
 * or more subscribers. It is currently used for working with the test
 * framework.
 *
 * In the future, our goal is to make this into a 'batteries included'
 * framework for developing `react`/`redux`/`lo_event` applications
 * which embodies good design practices for this domain.
 *
 * Our goal is NOT to be universal. Integrating `lo_event` into an
 * exiting `redux` workflow is ≈25 lines of code. This framework is
 * opinionated, and if there's a clash of opinions, you're better
 * off writing those 25 lines.
 *
 * Beyond test cases, the major use case is to make the development of
 * a broad class of simple educational activites, well, simple. For
 * larger applications, it probably makes more sense to start with
 * vanilla `react`/`redux`/`lo_event` without using this file, to just
 * use bits and pieces, or to treat this code as an examplar.
 */
import * as redux from 'redux';

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

function store_last_event_reducer(state = {}, action) {
  return { ...state, event: action.payload };
};

function lock_fields_reducer(state = {}, action) {
  const payload = JSON.parse(action.payload);
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
}

const REDUCERS = {
  'EMIT_EVENT': [store_last_event_reducer],
  'EMIT_LOCKFIELDS': [lock_fields_reducer]
}

// Reducer function
const reducer = (state = {}, action) => {
  let payload;

  return REDUCERS[action.type] ? composeReducers(...REDUCERS[action.type])(state, action) : state;
};


const eventQueue = [];
export let store = redux.createStore(reducer);
let promise = null;
let previousEvent = null;
let lockFields = null;
let eventSubscribers = [];

/*
  Compose reducers takes a dynamic number of reducers as arguments and
  returns a new reducer function. This applies each reducer to the
  state in the order they are provided, ultimately returning the
  final state after all reducers have been applied.

  Example usage:
  ```
  const rootReducer = composeReducers(reducer1, reducer2, reducer3);
  const finalState = rootReducer(initialState, { type: 'SOME_ACTION' });
  ```
*/
function composeReducers(...reducers) {
  return (state, action) => reducers.reduce(
    (currentState, reducer) => reducer(currentState, action),
    state
  );
}


function initializeStore () {
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
