import React from 'react';

import { useState } from 'react'; // For debugging / dev. Should never be used in final code.
import { useDispatch } from 'react-redux';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';

import * as lo_event from 'lo_event';

import { useComponentSelector, extractChildrenText } from './utils.js';

import { Spinner, Button } from './base_components';

// Debug log function. This should perhaps go away / change / DRY eventually.
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };

export const UPDATE_LLM_RESPONSE = 'UPDATE_LLM_RESPONSE';

export function LLMPrompt({children}) {
  return <></>;
}


const LLMDialog = ({ children, id, onCloseDialog }) => {
  return (
    <dialog open onClose={onCloseDialog}>
      <div style={styles.dialogHeader}>
        <h2 style={styles.dialogTitle}>Prompt Title</h2>
        <span style={styles.dialogClose} onClick={onCloseDialog}>
          <FontAwesomeIcon icon={faTimes} />
        </span>
      </div>
      <div style={styles.dialogContent}>
        {children}
      </div>
    </dialog>
  );
}


export const ActionButton = ({ children, target, showPrompt = true, ...props }) => {
  const [dialogVisible, setDialogVisible] = useState(false);

  const onClick = () => {
    React.Children.forEach(children, (child) => {
      dclog("ept", children);
      if (React.isValidElement(child) && child.type === LLMPrompt) {
        const promptText = extractChildrenText(child);
        run_llm(child.props.target, { prompt: promptText });
      }
    });
  };

  const onPromptClick = () => {
    setDialogVisible(true);
  };

  const onCloseDialog = () => {
    setDialogVisible(false);
  };

  return (
    <>
      <Button onClick={onClick} {...props}>
        {children}
      </Button>
      {showPrompt && <span onClick={onPromptClick} style={styles.questionMark}>
                       <FontAwesomeIcon icon={faQuestionCircle} />
                     </span>}
      {dialogVisible && (
        <LLMDialog onCloseDialog={onCloseDialog}> {children} </LLMDialog>
      )}
    </>
  );
};

// Obsolete name
export const LLMButton = ActionButton;

export const LLMFeedback = ({children, id}) => {
  const dispatch = useDispatch();
  let feedback = useComponentSelector(id, s => s?.value ?? '');
  let state = useComponentSelector(id, s => s?.state ?? LLM_INIT);

  /*useEffect(
    () => dispatch(() => run_llm(id, {prompt: 'What day is it today'}))
    , []);*/

  return (
    <div>
      <center> 🤖 </center>
      {state === LLM_RUNNING ? (<Spinner/>) : feedback}
    </div>
  );
};

const LLM_INIT = 'LLM_INIT';
const LLM_RESPONSE = 'LLM_RESPONSE';
const LLM_ERROR = 'LLM_ERROR';
const LLM_RUNNING = 'LLM_RUNNING';

const run_llm = (target, llm_params) => {
  lo_event.logEvent(
    UPDATE_LLM_RESPONSE, {
      id: target,
      state: LLM_RUNNING
    });
  fetch('/api/llm', {
    method: 'POST',
    body: JSON.stringify(llm_params),
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => response.json())
    .then((data) => {
      dclog(data);
      lo_event.logEvent(
        UPDATE_LLM_RESPONSE, {
          id: target,
          value: data.response,
          state: LLM_RESPONSE
        });
    })
    .catch((error) => {
      lo_event.logEvent(
        UPDATE_LLM_RESPONSE, {
          id: target,
          value: "Error calling LLM",
          state: LLM_ERROR
        });
      console.error(error);
    });
};

// This will go in a CSS file later. For dev.
const styles = {
  questionMark: {
    fontSize: '0.75rem',
    color: 'blue',
    cursor: 'pointer',
    marginRight: '0.75rem',
  },
  dialog: {
    position: "fixed",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    boxShadow: "0 0 5px rgba(0, 0, 0, 0.2)",
    borderRadius: "5px",
    padding: "20px",
    backgroundColor: "white",
    zIndex: "999",
  },
  dialogHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "10px",
  },
  dialogTitle: {
    margin: "0",
  },
  dialogClose: {
    cursor: "pointer",
  },
  dialogContent: {
    marginBottom: "20px",
  },
};

