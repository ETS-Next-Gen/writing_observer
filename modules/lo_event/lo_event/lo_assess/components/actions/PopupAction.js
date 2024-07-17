import * as util from '../../util.js';
import { createAction } from '../actions.js';

export const PopupAction = createAction({
  name: "PopupAction",
  f: ({node}) => alert(util.extractChildrenText(node))
});
