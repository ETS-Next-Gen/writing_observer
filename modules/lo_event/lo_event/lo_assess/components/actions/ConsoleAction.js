import * as util from '../../util.js';
import { createAction } from '../actions.js';

export const ConsoleAction = createAction({
  name: "ConsoleLog",
  f: ({node}) => console.log(util.extractChildrenText(node))
});
