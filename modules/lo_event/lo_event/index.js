import * as logManager from './lo_event.js';
import { reduxLogger } from './reduxLogger.js';
import { websocketLogger } from './websocketLogger.js';
import { consoleLogger } from './consoleLogger.js';
import { nullLogger } from './nullLogger.js';
import xapi from './xapi.cjs';

const loggers = {
  reduxLogger, websocketLogger, consoleLogger, nullLogger
};

export { logManager, loggers, xapi };
