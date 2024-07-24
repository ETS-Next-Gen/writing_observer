// Basic components. This should depend on no other component files.

import React from 'react';

import { useEffect } from 'react';
import { useDispatch } from 'react-redux';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faAngleDown, faAngleRight, faExclamationTriangle, faQuestionCircle, fasQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';
import { faCheckCircle, faTimesCircle, faDotCircle } from '@fortawesome/free-solid-svg-icons';

import * as lo_event from 'lo_event';
import * as reduxLogger from 'lo_event/lo_event/reduxLogger.js';

import { useComponentSelector, useSettingSelector } from './utils.js';
import { library } from '@fortawesome/fontawesome-svg-core';

// Debug log function. This should perhaps go away / change / DRY eventually.
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };

library.add(faCheckCircle, faDotCircle, faTimesCircle, faQuestionCircle);

// Pure CSS spinner taken from public domain spinners at loading.io/css
// https://github.com/loadingio/css-spinner/blob/master/README.md
export const Spinner = () => (
  <div className="spinner">
    <div></div>
    <div></div>
    <div></div>
  </div>
);


export function Button( {...props} ) {
  const className = props.className ?? "blue-button";
  return <button className={className} {...props}/>;
}


export function ResetButton({children, ...props}) {
  return (
    <Button onClick={() => reduxLogger.setState({})} {...props} >
      { children }
    </Button>
  );
}


export function List({ component: Component, count, id, componentProps }) {
  return (
    <div>
      {Array.from(Array(count)).map((_, index) => (
        <Component key={index} id={`${id}.${index}`} {...componentProps} />
      ))}
    </div>
  );
}

// Rotating triangle for hiding / showing e.g. accordion regions
export function ShowHideToggle({visible}) {
  return (<FontAwesomeIcon icon={visible ? faAngleDown : faAngleRight} aria-hidden="true" />);
}

const Error = ({ children }) => {
  return (
    <div className="error">
      <FontAwesomeIcon icon={faExclamationTriangle} size="2x" />
      <span> children </span>
    </div>
  );
};


export function GitEditLink({ target }) {
  const base_url = useSettingSelector("git_links_base");
  const visible = useSettingSelector("git_links_visible");

  if (!visible) {
    return null; // If visible is false, return nothing
  }

  if (visible && !base_url) {
    return <Error>git links visible, but git URL not configured</Error>;
  }

  return (
    <a className="edit-github edit-resources" href={base_url+target}>
      <FontAwesomeIcon icon={faEdit} />
    </a>
  );
}

export const DebugJSON = ({ label = '', children }) => {
  const isDebugVisible = useSettingSelector("debug"); // TODO: Better setting setup

  return (
    <>
      {isDebugVisible && (
        <>
          <code style={{ display: 'block', fontSize: '14px', color: 'red' }}>
          {label && <h4>{label}</h4>}
            { JSON.stringify(children) }
          </code>
        </>
      )}
    </>
  );
};

export const PulsedFeedback = ({ feedback, attempts, correct }) => {
  const css_parity = attempts % 2 + 1; // We toggle identical CSS to get animations.
  if (feedback) {
    return <p className={ `pulse-${correct}-${css_parity}` }>{feedback}</p>;
  }

  return null;
};

export function CorrectnessIcon( { state } ) {
  const iconMap = {
    correct: 'check-circle',
    incorrect: 'times-circle',
    invalid: 'question-circle',
    unanswered: 'dot-circle',
  };
  const icon = iconMap?.[state] ?? iconMap.unanswered;

  return <FontAwesomeIcon icon={icon} />;
}
