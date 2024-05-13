import * as util from '../util.js';

export function createAction({f, name}) {
  let Action = ({props}) => (<></>);
  Action.isAction = true;
  Action.action = f;
  Object.defineProperty(Action, 'name', {value: name, writable: false});
  return Action;
}

export const PopupAction = createAction({
  name: "PopupAction",
  f: ({node}) => alert(util.extractChildrenText(node))
});

export const ConsoleLog = createAction({
  name: "ConsoleLog",
  f: ({node}) => console.log(util.extractChildrenText(node))
});

export const TargetAction = createAction({
  name: "TargetAction",
  f: ({ node }) => {
    const message = util.extractChildrenText(node);
    const target = node.props.target;
    console.log(target, message);
  }
});


/*
export function LLMPrompt({children}) {
  return <></>;
}

export const reset=() => reduxLogger.setState({});
*/