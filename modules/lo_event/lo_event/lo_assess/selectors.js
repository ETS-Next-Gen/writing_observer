import React from 'react';
import * as idResolver from './idResolver';

import { shallowEqual, useSelector } from 'react-redux';

function normalizeOptions(arg) {
  // If undefined
  if (arg === undefined) return { fallback: undefined, equalityFn: undefined };

  // If it's a function, assume equalityFn
  if (typeof arg === 'function') return { fallback: undefined, equalityFn: arg };
  // If it's an object, assume { fallback?, equalityFn? }
  if (typeof arg === 'object') return arg;

  // Otherwise invalid
  throw new Error(`[selectors] Invalid selector options: ${arg}`);
}

export function useApplicationSelector(selector = s => s, efn) {
  return useSelector(
    state => selector(state?.application_state),
    efn
  );
}

// Get the state for any component, by ID.
export function useComponentSelector(id, selector = s => s, efn) {
  return useApplicationSelector(
    s => selector(s?.component_state?.[idResolver.reduxId(id)]),
    efn
  );
}

export function useSettingSelector(setting, efn) {
  return useSelector(
    state => state?.settings?.[setting],
    efn
  );
}

export function useFieldSelector(id, field, fallback = undefined) {
  return useComponentSelector(id, s => s?.[field] ?? fallback);
}
