/**
 * LOConnectionLastUpdated is a helper function for displaying
 * connection information and last received message information
 * about a websocket.
 * 
 * Usage:
 * ```js
 * const { readyState, message, } = LOConnection({ url, dataScope }); // or some other websocket
 * return ( <LOConnectionLastUpdated message={message} readyState={readyState} /> );
 * ```
 */
import React, { useState, useEffect } from 'react';

function renderTime(t) {
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
  var seconds = Math.floor(t) % 60;
  var minutes = Math.floor(t / 60) % 60;
  var hours = Math.floor(t / 3600) % 60;
  var days = Math.floor(t / 3600 / 24);

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

function renderReadableTimeSinceUpdate(timeDifference) {
    if (timeDifference < 5) {
      return 'Just now'
    }
    return `${renderTime(timeDifference)} ago`
}

export const LOConnectionLastUpdated = ({ message, readyState }) => {
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastUpdatedMessage, setLastUpdatedMessage] = useState('');

  const icons = ['fas fa-sync-alt', 'fas fa-check text-success', 'fas fa-sync-alt', 'fas fa-times text-danger'];
  const titles = ['Connecting to server', 'Connected to server', 'Closing connection', 'Disconnected from server'];

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
      } else { setLastUpdatedMessage('Never') }
    }, 1000);
    return () => clearInterval(interval); // Cleanup interval on unmount
  }, [lastUpdated]);

  return (
    <div title={titles[readyState]}>
      <i className={icons[readyState]} />
      <span className='ms-1'>{lastUpdatedMessage}</span>
    </div>
  );
};
