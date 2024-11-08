// Demo to show the Websocket

'use client';
// @refresh reset

// We need to import this to call init() for now
import { } from '../components.js';

import React, { useState, useEffect } from 'react';
import { LOConnection, LOConnectionLastUpdated, LOConnectionDataManager, Button } from 'lo_event/lo_event/lo_assess/components/components.jsx';

export default function Home ({ children }) {
  const decoded = {};
  decoded.course_id = '123456';
  const dataScope = {
    wo: {
      execution_dag: 'writing_observer',
      target_exports: ['docs_with_nlp_annotations'],
      kwargs: decoded
    }
  };

  const [userData, setUserData] = useState({});
  const [errors, setErrors] = useState({});

  const { readyState, message, error, sendMessage, openConnection, closeConnection } = LOConnection({ url: 'ws://localhost:8888/wsapi/communication_protocol', dataScope });
  const handleDataUpdate = ({ dataObject, errors }) => {
    setUserData(dataObject);
    setErrors(errors);
  };
  return (
    <div>
      <h1>WebSocket Connection Page</h1>
      <div>
        <LOConnectionLastUpdated message={message} readyState={readyState} />
        <LOConnectionDataManager message={message} onDataUpdate={handleDataUpdate} />
      </div>
      <div>
        <Button onClick={() => sendMessage(JSON.stringify(dataScope))} disabled={readyState !== WebSocket.OPEN}>
          Re-send dataScope to Server
        </Button>
        <Button onClick={openConnection} disabled={readyState === WebSocket.OPEN || readyState === WebSocket.CONNECTING}>
          Open Connection
        </Button>
        <Button onClick={closeConnection} disabled={readyState !== WebSocket.OPEN}>
          Close Connection
        </Button>
      </div>
      <div>
        <h2>User Data</h2>
          {Object.keys(userData).length > 0
            ? (<pre>{JSON.stringify(userData, null, 2)}</pre>)
            : (<p>No user data available.</p>)
          }
      </div>
      {Object.keys(errors).length > 0 && (
        <div style={{ color: 'red' }}>
          <h2>Errors</h2>
          <pre>{JSON.stringify(errors, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
