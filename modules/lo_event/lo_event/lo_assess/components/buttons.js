import React from 'react';

import * as reduxLogger from '../../reduxLogger.js';
import * as util from '../util.js';

/*
 * Parent of all buttons!
 */
export function Button( {...props} ) {
  const className = props.className ?? "blue-button";
  return <button className={className} {...props}/>;
}

/*
 * Reset the system state
 *
 * This should be folded into action button?
 */
export function ResetButton({children, ...props}) {
  return (
    <Button onClick={() => reduxLogger.setState({})} {...props} >
      { children }
    </Button>
  );
}


export function executeChildActions(children) {
  console.log("Running child actions");
  console.log(children);
  React.Children.forEach(children, (child) => {
    console.log("eca:", child);
    if (React.isValidElement(child)) {
      console.log("eca.type:", child.type);
      console.log("eca.type.isaction:", child.type.isAction);
      console.log("ive:", React.isValidElement(child));
    }
    if (React.isValidElement(child) && child.type.isAction) {
      console.log("Running executor");
      child.type.action( { node: child } );
    }
  });
}

/*
 * 
 */
export const ActionButton = ({ children, target, systemPrompt, showPrompt = true, ...props }) => {
  const onClick = () => executeChildActions(children);
  return (
      <Button onClick={onClick} {...props} > { children } </Button>
  );
}
