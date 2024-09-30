/**
 * LOConnection is a websocket component used for connecting to
 * the communication protocl on Learning Observer.
 *
 * The server expects some data before it will start sending messages.
 * When the connection opens, LOConnection will send the `dataScope`,
 * if available, to initiate receiving messages from the server.
 * Otherwise, users should use the `sendMessage` function to provide
 * data to LO.
 *
 * LOConnection exposes the following items:
 * - `sendMessage`: function to send messages to the server
 * - `message`: the most recent message received
 * - `error`: any errors that occured
 * - `readyState`: the current status of the websocket connection
 */
import { useEffect, useRef, useState } from 'react';

export const LOConnection = ({
  url, dataScope
}) => {
  const [readyState, setReadyState] = useState(WebSocket.CLOSED);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const clientRef = useRef(null);

  useEffect(() => {
    const protocol = { 'http:': 'ws:', 'https:': 'wss:' }[window.location.protocol];
    const newUrl = url || `${protocol}//${window.location.hostname}:${window.location.port}/wsapi/communication_protocol`;
    const client = new WebSocket(newUrl);
    clientRef.current = client;

    client.onopen = () => {
      setReadyState(WebSocket.OPEN);
      if (typeof dataScope !== 'undefined') {
        client.send(JSON.stringify(dataScope));
      }
    };

    client.onmessage = (event) => {
      setMessage(event.data);
    };

    client.onerror = (event) => {
      setError(event.message);
    };

    client.onclose = () => {
      setReadyState(WebSocket.CLOSED);
    };

    return () => {
      if (clientRef.current) {
        clientRef.current.close();
      }
    };
  }, [url]);

  // Function to send a message via WebSocket
  const sendMessage = (message) => {
    if (clientRef.current && readyState === WebSocket.OPEN) {
      clientRef.current.send(message);
    } else {
      console.warn('WebSocket is not open. Ready state:', readyState);
    }
  };

  return { sendMessage, message, error, readyState };
};
