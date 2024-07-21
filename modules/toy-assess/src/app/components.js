/*
 * This file contains generic components and most of the machinery
 * behind the system. The goal is to gradually make the main page file
 * simple enough for a relatively non-technical person to edit, and then
 * to abstract much of it into data files.
 *
 * To do that, we are happy to have extra complexity here.
 */

import React from 'react';

import * as lo_event from 'lo_event';
import * as reduxLogger from 'lo_event/lo_event/reduxLogger.js';
import * as debug from 'lo_event/lo_event/debugLog.js';

import { consoleLogger } from 'lo_event/lo_event/consoleLogger.js';

import { registerReducer } from 'lo_event/lo_event/reduxLogger.js';

import { updateResponseReducer } from './utils.js';

import { UPDATE_LLM_RESPONSE } from './llm_components';
import { UPDATE_INPUT } from './input_types';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';

import './base-style.css';
import './sidebar-panel.css';
import './button.css';

export const STORE_VARIABLE = 'STORE_VARIABLE';
export const SHOW_SECTION='SHOW_SECTION';


lo_event.init(
  "org.ets.sba",
  "0.0.1",
  [consoleLogger(), reduxLogger.reduxLogger([], {})],
  {
	  debugLevel: debug.LEVEL.EXTENDED,
	  debugDest: [debug.LOG_OUTPUT.CONSOLE],
	  useDisabler: false,
	  queueType: lo_event.QueueType.IN_MEMORY
  }
);

lo_event.go();

// We don't use this as a decorator here since we occasionally want to
// register new events with the same reducer elsewhere.
registerReducer(
  [UPDATE_INPUT, UPDATE_LLM_RESPONSE, STORE_VARIABLE, SHOW_SECTION],
  updateResponseReducer
);

