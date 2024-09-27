// Demo to show the Websocket

'use client';
// @refresh reset

// We need to import this to call init() for now
import { } from '../components.js';

import React, { useState, useEffect } from 'react';
import { LOConnection, LOConnectionLastUpdated, Button } from 'lo_event/lo_event/lo_assess/components/components.jsx';

export default function Home ({ children }) {
  const decoded = {};
  decoded.course_id = '123456';
  const dataScope = {
    wo: {
      execution_dag: 'wo_bulk_essay_analysis',
      target_exports: ['gpt_bulk'],
      kwargs: decoded
    }
  };

  const { readyState, message, error, sendMessage } = LOConnection({ url: 'ws://localhost:8888/wsapi/communication_protocol', dataScope });

  return (
    <div>
      <h1>WebSocket Connection Page</h1>
      <div>
        <LOConnectionLastUpdated message={message} readyState={readyState} />
      </div>
      <div>
        <Button onClick={() => sendMessage(JSON.stringify(dataScope))} disabled={readyState !== WebSocket.OPEN}>
          Re-send dataScope to Server
        </Button>
      </div>
      <div>
        <h2>Received Message</h2>
        {message ? <p>{message}</p> : <p>No messages received yet.</p>}
      </div>
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
    </div>
  );
};
