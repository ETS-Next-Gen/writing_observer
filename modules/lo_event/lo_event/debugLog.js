function sendToServer (sendEvent) {
  const counts = {};
  return function (messageType, message, stackTrace) {
    if (!Object.prototype.hasOwnProperty.call(counts, messageType)) {
      counts[messageType] = 0;
    }
    counts[messageType]++;
    if (Math.log10(counts[messageType]) % 1 === 0) {
      const payload = { message_type: messageType, message };
      if (stackTrace) {
        payload.stack = stackTrace;
      }
      sendEvent('debug', payload);
    }
  };
}

function sendToConsole (messageType, message, stackTrace) {
  const stackOutput = stackTrace ? `\n  Stacktrace: ${stackTrace}` : '';
  console.log(`${messageType}, ${message} ${stackOutput}`);
}

export const DESTINATIONS = {
  CONSOLE: sendToConsole,
  SERVER: sendToServer
};

export const LEVEL = {
  NONE: 'none',
  SIMPLE: 'simple',
  EXTENDED: 'extended'
};

let debugLevel = LEVEL.SIMPLE;

let debugDestinations = [DESTINATIONS.CONSOLE];

export function setLevel (level) {
  if (![LEVEL.NONE, LEVEL.SIMPLE, LEVEL.EXTENDED].includes(level)) {
    throw new Error(`Invalid debug log type ${level}`);
  }
  debugLevel = level;
}

export function setDestinations (dst) {
  debugDestinations = dst;
}

export function info (log, stack) {
  const formattedLog = formatLog(log);
  for (const logDestination of debugDestinations) {
    logDestination('info', formattedLog, stack);
  }
}

export function error (log, error) {
  const formattedLog = formatLog(log);
  for (const logDestination of debugDestinations) {
    logDestination(error.name || 'Error', formattedLog, error.stack);
  }
}

function formatLog (text) {
  let message;
  if (debugLevel === LEVEL.NONE) {
    return;
  } else if (debugLevel === LEVEL.SIMPLE) {
    message = text;
  } else if (debugLevel === LEVEL.EXTENDED) {
    const stackTrace = getStackTrace();
    const time = new Date().toISOString();
    message = `${time}: ${text}\n${stackTrace.padEnd(60)}`;
  }
  return message;
}

function getStackTrace () {
  const stack = new Error().stack.split('\n');
  const stackTrace = [stack[2], stack[3], stack[4]].join('\n');
  return stackTrace;
}
