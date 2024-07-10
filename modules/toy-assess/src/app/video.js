import React from 'react';
import { useState, useRef } from 'react';

import * as lo_event from 'lo_event';

import { useComponentSelector, updateResponseReducer, useData } from './utils.js';
import { registerReducer } from 'lo_event/lo_event/reduxLogger.js';

import { Spinner } from './base_components.js';

import './subtitles.css';

export const VIDEO_TIME_EVENT = 'VIDEO_TIME_EVENT';

const VIDEOELEMENT = 'VIDEOELEMENT';

registerReducer(
  [VIDEO_TIME_EVENT],
  updateResponseReducer
);

export const VideoElement = (props) => {
  // Event listener to log events to console
  const id = props.id;
  const timestamp = useComponentSelector(id, s => s?.timeStamp ?? 0);
  const source = useComponentSelector(id, s => s?.source ?? 0);
  const videoRef = useRef(null);

  if(source != VIDEOELEMENT) {
    videoRef && videoRef.current && (videoRef.current.currentTime = timestamp);
  }

  const handleEvent = (e) => {
    lo_event.logEvent('VIDEO_'+e.type.toUpperCase(), { id, timestamp: e.target.currentTime });
    console.log(`Event: ${e.type}`);
    console.log(e);
  };

  const [currentTime, setCurrentTime] = useState(0);

  const handleTimeUpdate = (e) => {
    const video = e.target;
    setCurrentTime(video.currentTime);
    lo_event.logEvent(
      VIDEO_TIME_EVENT, {
        id,
        timeStamp: video.currentTime,
        source: VIDEOELEMENT
      });
  };

  return (
    <>
      <video
        src={props.src}
        width={props.width}
        height={props.height}
        controls
        ref={videoRef}
        onPlay={handleEvent}
        onPause={handleEvent}
        onWaiting={handleEvent}
        onEnded={handleEvent}
        onLoadedMetadata={handleEvent}
        onError={handleEvent}
        onSeeked={handleEvent}
    // onSeeking={handleEvent}  <-- Useful, but massive number of events
        onStalled={handleEvent}
        onTimeUpdate={handleTimeUpdate}
    // Add more event listeners as needed
      />
      <p>Current Time: {currentTime.toFixed(2)}</p>
    </>
  );
};

// For src, the subtitles are a JSON file, as created by
// Whisper. Eventually, we should support more standard formats.
//
// E.g.
// import * as vtt from 'vtt.js';
// let parser = new vtt.WebVTT.Parser(window);
export const Subtitles = ({ src, subtitles, id }) => {
  const timestamp = useComponentSelector(id, s => s?.timeStamp ?? 0);

  subtitles = useData({id, key: 'subtitles', url: src, override: subtitles, modifier: (d) => d.segments});
  const subtitlesContainerRef = React.useRef(null);

  const scrollToActive = (videoTime) => {
    const activeSubtitle = subtitlesContainerRef.current.querySelector('.subtitle-active');
    if (activeSubtitle) {
      activeSubtitle.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleSubtitleClick = (subtitle) => {
    // Update the video time to the start timestamp of the clicked subtitle
    lo_event.logEvent(VIDEO_TIME_EVENT, {
      id,
      timeStamp: subtitle.start,
      source: 'SUBTITLES'
    });
  };

  // Call scrollTo() with the desired scroll position whenever scrollPosition prop changes
  React.useEffect(() => {
    scrollToActive(timestamp);
  }, [timestamp]);

  if(!subtitles) {
    return <div id="subtitlesContainer" className="subtitles-container" ref={subtitlesContainerRef}><Spinner/></div>;
  }

  return (
    <div id="subtitlesContainer" className="subtitles-container" ref={subtitlesContainerRef}>
      {subtitles.map((subtitle, index) => {
        let subtitleClass = "subtitle";
        if(subtitle.start<=timestamp && timestamp<subtitle.end) {
          subtitleClass += " subtitle-active";
        }
        return (
          <div key={index} className={subtitleClass} onClick={() => handleSubtitleClick(subtitle)}>
            <div className="subtitle-time">{formatTime(subtitle.start) + '➔' + formatTime(subtitle.end)} </div>
            <div className="subtitle-text">{subtitle.text}</div>
          </div>
        );
      })}
    </div>
  );
};


// TODO:
// * Move to util.
// * We also have this somewhere else, so probably abstract out into a common library.
// * Or find this in a utility library function somewhere.
function formatTime(seconds) {
  // Calculate hours, minutes, and remaining seconds
  var hours = Math.floor(seconds / 3600);
  var minutes = Math.floor((seconds % 3600) / 60);
  var remainingSeconds = (seconds % 60).toFixed(2);
  
  // Format hours, minutes, and remaining seconds to include leading zeros
  var formattedHours = hours.toString().padStart(2, '0');
  var formattedMinutes = minutes.toString().padStart(2, '0');
  var formattedSeconds = remainingSeconds.padStart(5, '0');
  
  // Concatenate and return the formatted time
  if (hours > 0) {
    return `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;
  } else {
    return `${formattedMinutes}:${formattedSeconds}`;
  }
}
