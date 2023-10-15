// Most of this code is not finished. It outlines the general planned
// logic, but we need to make APIs consistent (and asynchronous) in
// all three cases.

// thunkStorage mirrors the capability of `chrome.storage.sync`
// this is used mostly for testing purposes
const thunkStorage = {
  data: {},
  set: function (items, callback) {
    this.data = { ...this.data, ...items };
    if (callback) callback();
  },
  get: function (keys, callback) {
    let result = {};
    if (Array.isArray(keys)) {
      keys.forEach(key => {
        if (this.data.hasOwnProperty(key)) {
          result[key] = this.data[key];
        }
      })
    } else if (typeof keys === 'string') {
      if (this.data.hasOwnProperty(keys)) {
        result[keys] = this.data[keys];
      }
    } else {
      result = { ...this.data };
    }
    if (callback) callback(result);
  }
}

export let storage;

let b;

if (typeof browser !== 'undefined') {
  b = browser;
} else if (typeof chrome !== 'undefined') {
  b = chrome;
} else if (typeof firefox !== 'undefined') {
  b = firefox;
}

if (typeof b !== 'undefined') {
  if (b.storage && b.storage.sync) {
    storage = b.storage.sync;
  } else if (b.storage && b.storage.local) {
    storage = b.storage.local;
  }
} else if (typeof localStorage !== 'undefined') {
  // Add compatibility modifications for localStorage
  localStorage.get = localStorage.getItem;
  localStorage.set = localStorage.setItem;
  storage = localStorage;
} else if (typeof window !== 'undefined' && typeof window.localStorage !== 'undefined') {
  // Add compatibility modifications for window.localStorage
  window.localStorage.get = window.localStorage.getItem;
  window.localStorage.set = window.localStorage.setItem;
  storage = window.localStorage;
} else {
  // If none of the above options exist, fall back to thunkStorage or exit gracefully
  storage = thunkStorage;
}
