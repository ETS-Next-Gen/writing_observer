import React from 'react';

/*
 *
 */

export const extractChildrenText = (element) => {
  if (typeof element === "string") {
    return element.trim();
  }
  const extractElementText = (element) => {
    if (typeof element === "string") {
      return element.trim();
    } else if (React.isValidElement(element)) {
      return element.type.eval(element);
    }
    return "";
  };

  const { children } = element.props;
  const extractedChildren = React.Children.map(children, (element) => extractElementText(element));
  return extractedChildren.join("");
};
