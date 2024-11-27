/**
 * LOConnectionLastUpdated is a helper function for displaying
 * connection information and last received message information
 * about a websocket.
 *
 * Usage:
 * ```js
 * const { connectionStatus, message, } = LOConnection({ url, dataScope }); // or some other websocket
 * return ( <LOConnectionLastUpdated message={message} connectionStatus={connectionStatus} /> );
 * ```
 */
import React from 'react';
import { useState, useEffect } from 'react';
import { LO_CONNECTION_STATUS } from '../constants/LO_CONNECTION_STATUS';

function renderTime (t) {
  /*
  Convert seconds to a time string.

  Compact representation.
    10     ==> 10s
    125    ==> 2m
    3600   ==> 1h
    7601   ==> 2h
    764450 ==> 8d

  TODO this code exists in `liblo.js` include these functions
  or migrate them to a utilities file in this LO Event.
   */
  const seconds = Math.floor(t) % 60;
  const minutes = Math.floor(t / 60) % 60;
  const hours = Math.floor(t / 3600) % 60;
  const days = Math.floor(t / 3600 / 24);

  if (days > 0) {
    return String(days) + 'd';
  }
  if (hours > 0) {
    return String(hours) + 'h';
  }
  if (minutes > 0) {
    return String(minutes) + 'm';
  }
  if (seconds > 0) {
    return String(seconds) + 's';
  }
  return '-';
}

function renderReadableTimeSinceUpdate (timeDifference) {
  if (timeDifference < 5) {
    return 'Just now';
  }
  return `${renderTime(timeDifference)} ago`;
}

export const LOConnectionLastUpdated = ({ message, connectionStatus }) => {
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastUpdatedMessage, setLastUpdatedMessage] = useState('');

  const icons = {
    [LO_CONNECTION_STATUS.UNINSTANTIATED]: 'fas fa-circle',
    [LO_CONNECTION_STATUS.CONNECTING]: 'fas fa-sync-alt',
    [LO_CONNECTION_STATUS.OPEN]: 'fas fa-check text-success',
    [LO_CONNECTION_STATUS.CLOSING]: 'fas fa-sync-alt',
    [LO_CONNECTION_STATUS.CLOSED]: 'fas fa-times text-danger'
  };
  const titles = {
    [LO_CONNECTION_STATUS.UNINSTANTIATED]: 'Uninstantiated',
    [LO_CONNECTION_STATUS.CONNECTING]: 'Connecting to server',
    [LO_CONNECTION_STATUS.OPEN]: 'Connected to server',
    [LO_CONNECTION_STATUS.CLOSING]: 'Closing connection',
    [LO_CONNECTION_STATUS.CLOSED]: 'Disconnected from server'
  };

  // Set last updated time when new message arrives
  useEffect(() => {
    if (message) {
      setLastUpdated(new Date());
    }
  }, [message]);

  // Every second update last updated message
  useEffect(() => {
    const interval = setInterval(() => {
      if (lastUpdated) {
        const now = new Date();
        const timeDifference = Math.floor((now - lastUpdated) / 1000); // Time difference in seconds
        setLastUpdatedMessage(renderReadableTimeSinceUpdate(timeDifference));
      } else { setLastUpdatedMessage('Never'); }
    }, 1000);
    return () => clearInterval(interval); // Cleanup interval on unmount
  }, [lastUpdated]);

  return (
    <div title={titles[connectionStatus]}>
      <i className={icons[connectionStatus]} />
      <span className='ms-1'>{lastUpdatedMessage}</span>
    </div>
  );
};
