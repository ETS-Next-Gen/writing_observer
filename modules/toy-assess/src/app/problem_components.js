import React from 'react';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faCheckCircle, faDotCircle, faTimesCircle, faQuestionCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';

import * as lo_event from 'lo_event';

import * as components from './components.js';
import { useComponentSelector } from './utils.js';

library.add(faCheckCircle, faDotCircle, faTimesCircle, faQuestionCircle);

export const CORRECTNESS = {
  CORRECT: 'correct',           // Got it right!
  INCORRECT: 'incorrect',       // Got it wrong :(
  PARTIAL: 'partially-correct', // Partial credit
  INVALID: 'invalid',           // Invalid submission (e.g. text for a numeric response, or a missing paren)
  UNANSWERED: 'unanswered',     // Student didn't answer
  GRADING: 'grading'            // Grading is in progress
};

export function AnswerIcon({id, base}) {
  const state = useComponentSelector(id) || base;

  const iconMap = {
    correct: 'check-circle',
    incorrect: 'times-circle',
    invalid: 'question-circle',
    unanswered: 'dot-circle',
    grading: 'spinner'
  };
  const icon = iconMap[state];

  return <FontAwesomeIcon icon={icon} />;
}

export function NumericInput( { base, id, children } ) {
  const state = useComponentSelector(id, s => s?.value) || base || "";

  const handleNumberChange = event => {
    lo_event.logEvent(
      components.UPDATE_INPUT, {
        id,
        value: event.target.value,
        // Do we want: cursor: event.target.selectionStart
      });
  };

  return (
    <div>
      <p>
        <input
          className="item-input"
          type="number"
          value={state.value}
          onChange={ handleNumberChange }
        />
        {children}
      </p>
    </div>
  );
}
