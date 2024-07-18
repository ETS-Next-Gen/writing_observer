import * as util from '../../util.js';
import { createAction } from '../actions.js';

export const TargetAction = createAction({
  name: "TargetAction",
  f: ({ node }) => {
    const message = util.extractChildrenText(node);
    const target = node.props.target;
    console.log(target, message);
  }
});