export const DESTINATIONS = {
  CONSOLE: 'console'
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
  if (!dst.every(item => [DESTINATIONS.CONSOLE].includes(item))) {
    throw new Error(`Invalid debug destination ${dst}`);
  }
  debugDestinations = dst;
}

export function log (log) {
  const formattedLog = formatLog(log);
  if (debugDestinations.includes(DESTINATIONS.CONSOLE)) {
    console.log(formattedLog);
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
    message = `${time}: ${stackTrace.padEnd(60)}\t${text}`;
  }
  return message;
}

function getStackTrace () {
  const stack = new Error().stack.split('\n');
  const stackTrace = [stack[2], stack[3], stack[4]].map(s => s.trim()).join('/');
  return stackTrace;
}
