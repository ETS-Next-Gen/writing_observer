import React from 'react';

/*
 * Parent of all buttons!
 */
export function Button( {...props} ) {
  const className = props.className ?? "blue-button";
  return <button className={className} {...props}/>;
}
