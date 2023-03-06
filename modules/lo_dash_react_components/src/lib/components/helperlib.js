import React from 'react';
import { debounce, once } from 'lodash';

export const CENTER = [0, 0];
export const RIGHT = [1, 90];
export const LEFT = [1, -90];
export const TOP = [1, 0];
export const BOTTOM = [1, -180];

/**
 * Returns a fraction indicating the staggered position of an item within a list.
 *
 * @param {number} index - The index of the element in the sequence (0-based).
 * @param {number} count - The total number of elements in the sequence.
 * @returns {number} The stagger value for the element, which is (index + 1) / (count + 1).
 *
 * For example, [stagger(0, 2), stagger(1,2)] would return [1/3, 2/3] (as a floating point)
 */
export function stagger(index, count) {
  return (index + 1) / (count + 1);
}


/**
 * djb2 is a hash function that produces a 32-bit hash value from a string.
 * The algorithm is attributed to Dan Bernstein.
 *
 * @param {string} str - The input string to hash.
 * @returns {number} The 32-bit hash value of the input string.
 */
export function djb2(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  return hash >>> 0;
}

/**
  * Update arrow positions on the page based on the current position
  * of their source and target elements.
  *
  * This function finds all elements with the class "zpd-arrow" and
  * updates their position based on the data attributes associated
  * with each arrow.
  *
  * These data attributes should include:
  *
  * * data-source: ID of element the arrow comes from
  * * data-target: ID of element the arrow points to
  * * data-wrapper: An element that is the parent of the
  *      source and target elements
  *
  * And may include:
  *
  * * data-source-offset and data-target-offset which should contain
  *   JSON-encoded arrays of two values [distance, angle], corresponding
  *   to the distance and angle from the center of the element
  *
  * This function calculates the distance, angle, and start and end
  * positions of the arrow, and updates the arrow's position on the
  * page accordingly.
  *
  * It should be run on page load, page resize, and any other time arrows
  * should be updated.
*/
export const updateArrowPositions = debounce(function() {
  const arrows = document.getElementsByClassName("arrow");
  
  Array.from(arrows).forEach((arrow) => {
    const source = document.getElementById(arrow.getAttribute('data-source'));
    const target = document.getElementById(arrow.getAttribute('data-target'));
    const offsetParent = arrow.offsetParent;

    const [source_distance, source_angle] = JSON.parse(arrow.getAttribute('data-source-offset') ?? '[0, 0]');
    const [target_distance, target_angle] = JSON.parse(arrow.getAttribute('data-target-offset') ?? '[0, 0]');
  
    // get positions of source and target elements
    const sourceRect = source.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    let sourceX = sourceRect.left + (sourceRect.width / 2); // + sourceRect.width a;
    let sourceY = sourceRect.top + (sourceRect.height / 2);
    let targetX = targetRect.left + (targetRect.width / 2);
    let targetY = targetRect.top + (targetRect.height / 2);

    targetX += target_distance * targetRect.width * Math.cos((target_angle-90) * Math.PI / 180)/2;
    targetY += target_distance * targetRect.height * Math.sin((target_angle-90) * Math.PI / 180)/2;
    sourceX += source_distance * sourceRect.width * Math.cos((source_angle-90) * Math.PI / 180)/2;
    sourceY += source_distance * sourceRect.height * Math.sin((source_angle-90) * Math.PI / 180)/2;


    // calculate the angle of the line
    const angle = Math.atan2(sourceY - targetY, sourceX - targetX);
    const degrees = angle * 180 / Math.PI-90;
    arrow.style.transform = `rotate(${degrees}deg)`;
    arrow.style.transformOrigin = "top left";

    // calculate the length of the line
    const distance = Math.sqrt(Math.pow(targetX - sourceX, 2) + Math.pow(targetY - sourceY, 2));
    arrow.style.height = distance + "px";

    // position the line at the center of the source element
    arrow.style.left = (targetX - offsetParent.offsetLeft) + "px";
    arrow.style.top = (targetY - offsetParent.offsetTop) + "px";
  });
}, 500, { leading: true, trailing: true });

export const initArrows=once(function() {
  window.addEventListener('resize', function(){
    updateArrowPositions();
  });
});


export function Arrow(props) {
  const { source, target, wrapper, sourceOffset = CENTER, targetOffset = CENTER } = props;
  return (
    <div 
      className="arrow"
      data-source={source}
      data-source-offset={JSON.stringify(sourceOffset)}
      data-target={target}
      data-target-offset={JSON.stringify(targetOffset)}
      data-wrapper={wrapper}
    ></div>
  );
}

/*** DEBUG CODE. This should eventually go away. */

/**
 * Creates a div covering the given element ID with absolute positioning.
 * The X overlay is intended for use during debugging and is not part of the final product.
 * It's helpful for understanding coordinates.
 *
 * @param {string} elementId - The ID of the element to create an X overlay for.
 */
function createXOverlay(elementId) {
  const targetElement = document.getElementById(elementId);
  if (!targetElement) {
    console.error(`Element with ID ${elementId} not found.`);
    return;
  }
  const xElement = document.createElement('div');
  xElement.textContent = 'X';
  xElement.style.position = 'absolute';
  xElement.style.top = `${targetElement.offsetTop}px`;
  xElement.style.left = `${targetElement.offsetLeft}px`;
  xElement.style.width = `${targetElement.offsetWidth}px`;
  xElement.style.height = `${targetElement.offsetHeight}px`;
  xElement.style.display = 'flex';
  xElement.style.justifyContent = 'center';
  xElement.style.alignItems = 'center';
  xElement.style.fontSize = '24px';
  xElement.style.fontWeight = 'bold';
  xElement.style.color = 'white';
  xElement.style.backgroundColor = 'red';
  xElement.style.borderRadius = '50%';
  xElement.style.cursor = 'pointer';
  xElement.addEventListener('click', () => {
    xElement.remove();
  });
  document.body.appendChild(xElement);
}

document.addEventListener("DOMContentLoaded", () => {
  updateArrowPositions();
  setTimeout(() => {
    console.log('X');
    updateArrowPositions();
  }, 1000);
});

document.addEventListener("resize", () => {
  updateArrowPositions();
});

document.addEventListener("load", () => {
  updateArrowPositions();
  setTimeout(() => {
    updateArrowPositions();
    console.log('X');
  }, 1000);
});