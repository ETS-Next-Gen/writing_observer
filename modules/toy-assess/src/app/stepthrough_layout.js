/*
  A layout for a linear flow.
  * This is currently implemented with next / prev buttons.
  * We might implement this in other ways in the future (e.g. as an early edX learning sequence).
 */

import React, { useState } from "react";
import { registerReducer } from 'lo_event/lo_event/reduxLogger.js';
import * as lo_event from 'lo_event';

import { useComponentSelector, updateResponseReducer } from "./utils.js";

export const STEPTHROUGH_NEXT = 'STEPTHROUGH_NEXT';
export const STEPTHROUGH_PREV = 'STEPTHROUGH_PREV';

registerReducer(
  [STEPTHROUGH_PREV, STEPTHROUGH_NEXT],
  updateResponseReducer
);

const StepThrough = ({ children, id }) => {
  let currentStep = useComponentSelector(id, s => s?.value ?? 0);

  let xmlNodes = React.Children.map(children, (child) => {
    if (typeof child.type !== "string") {
      return child;
    }
    return null;
  }).filter(Boolean);
  xmlNodes = children;


  const handleNextStep = () => {
    lo_event.logEvent(
      STEPTHROUGH_NEXT, {
        id,
        value: currentStep + 1
      });
  };

  const handlePreviousStep = () => {
    lo_event.logEvent(
      STEPTHROUGH_PREV, {
        id,
        value: currentStep - 1
      });
  };

  const renderRank = () => {
    const ranks = ["Apprentice", "Journeyman", "Master"];
    return <span>{ranks[currentStep]}</span>;
  };

  const renderProgressIndicator = () => {
    return (
      <progress value={currentStep + 1} max={xmlNodes.length}>
        Step {currentStep + 1} of {xmlNodes.length}
      </progress>
    );
  };

  return (
    <div style={{ width: "1280px" }}>
      <header style={{ backgroundColor: "black", padding: "10px" }}>
        <div style={{ textAlign: "center" }}>
          {renderRank()}
          {renderProgressIndicator()}
        </div>
      </header>

      {xmlNodes[currentStep]}

      <footer
        style={{
          backgroundColor: "black",
          padding: "10px",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <button onClick={handlePreviousStep} disabled={currentStep === 0}>
          Back
        </button>
        <button onClick={handleNextStep} disabled={currentStep === xmlNodes.length - 1}>
          Next
        </button>
        {/* Add any additional elements for the footer here */}
      </footer>
    </div>
  );
};

export default StepThrough;
