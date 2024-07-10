/*
 * This file contains generic components and most of the machinery
 * behind the system. The goal is to gradually make the main page file
 * simple enough for a relatively non-technical person to edit, and then
 * to abstract much of it into data files.
 *
 * To do that, we are happy to have extra complexity here.
 */

import React from 'react';

import { useSelector } from 'react-redux';
import { registerReducer, store } from 'lo_event/lo_event/reduxLogger.js';
import { useComponentSelector } from './utils.js';
import { useDispatch } from 'react-redux';
import { useEffect, useRef } from 'react';
import { useState } from 'react'; // For debugging / dev. Should never be used in final code.

import * as lo_event from 'lo_event';
import * as reduxLogger from 'lo_event/lo_event/reduxLogger.js';
import * as debug from 'lo_event/lo_event/debugLog.js';

import { consoleLogger } from 'lo_event/lo_event/consoleLogger.js';

import { activePage, extractChildrenText, updateResponseReducer } from './utils.js';

import { LLMPrompt, LLMButton, LLMFeedback, UPDATE_LLM_RESPONSE } from './llm_components';
export { LLMPrompt, LLMButton, LLMFeedback };

import { Button, ResetButton, List, ShowHideToggle, GitEditLink, DebugJSON } from './base_components';
import { TextInput, NumericInput, UnitInput, LineInput, RenderEquation, UPDATE_INPUT } from './input_types';
export { Button, ResetButton, NumericInput, UnitInput, LineInput, TextInput, List, ShowHideToggle, GitEditLink, DebugJSON };

import { MainPane, SideBarPanel } from './sidebar_layout';
export { MainPane, SideBarPanel };

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';

import './base-style.css';
import './sidebar-panel.css';
import './button.css';
import './spinner.css';

export const STORE_VARIABLE = 'STORE_VARIABLE';
export const SHOW_SECTION='SHOW_SECTION';

// Debug log function. This should perhaps go away / change / DRY eventually.
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };


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

export function Element({children}) {
  const id=children.trim();
  const value = useComponentSelector(id, s => s?.value);

  return <>{value}</>;
}

Element.eval = function(element) {
  const value=store.getState()?.application_state?.component_state?.[element.props.children.trim()]?.value;
  if(DEBUG) {
    console.log('eval', element.props.children.trim());
    console.log('eval', store.getState());
    console.log('eval', store.getState()?.application_state);
    console.log('eval', store.getState()?.application_state?.component_state);
    console.log('eval', store.getState()?.application_state?.component_state?.[element.props.children.trim()]);
    console.log('eval', store.getState()?.application_state?.component_state?.[element.props.children.trim()]?.value);
    console.log('eval', value);
  }
  return value;
}

export function Variable({children}) {
  return <></>;
}

export function StoreVariable({children, id}) {
  useEffect(
    () => {
      const text = extractChildrenText(children);
      dclog("store_var", id, text);
      lo_event.logEvent(
        STORE_VARIABLE, {
          id,
          value: text,
        });
    }, []);

  return <>{children}</>;
}

Variable.eval = function(element) {
  return "Variable eval";
};


export function ShowComponentButton({ id, target, hidetext, children }) {
  const componentState = useComponentSelector(target) || {};
  const visibility = componentState.isVisible || false;

  const handleButtonClick = () => {
    lo_event.logEvent(SHOW_SECTION, {
      id: target,
      isVisible: !visibility,
    });
  };

  return <Button onClick={handleButtonClick}>{ visibility ? (hidetext||'Hide') : children }</Button>;
}

export function HideableComponent({ id, children, slide }) {
  const componentState = useComponentSelector(id, s => s) || {};
  const visibility = componentState.isVisible || false;
  const componentRef = useRef(null);

  useEffect(() => {
    if (visibility && componentRef.current) {
      componentRef.current.scrollIntoView({
        alignToTop: true,
        behavior: 'smooth',
        block: 'start',
      });
    }
  }, [visibility]);

  if(!visibility) {
    return null;
  }

  return (
    <div ref={componentRef}>
      { children }
    </div>
  );
}

/*
  We're trying to figure out how to set up routes in an easy-to-use
  fashion. We are perhaps heading for something like this:

export function Switch({target, children}) {
  const activeRoute = React.Children.toArray(children).find(
    child => child.props.target === activePage
  );

  return activeRoute || null;
}

const Route = ({ target, children }) => {
  return React.Children.map(children, child =>
    React.cloneElement(child, { target })
  );
};
*/
