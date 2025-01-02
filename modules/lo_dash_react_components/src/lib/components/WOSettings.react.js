import React, { Component } from 'react';
import PropTypes from 'prop-types';

function generateNewHighlightColor () {
  // Generate random RGB values
  const r = Math.floor(Math.random() * 128) + 128; // 128-255 for brighter colors
  const g = Math.floor(Math.random() * 128) + 128;
  const b = Math.floor(Math.random() * 128) + 128;

  // Convert RGB to hex
  const hex = `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  return hex;
}

function sortOptionsIntoTree (options) {
  // Create a map of options by their ids
  const optionsMap = new Map();
  options.forEach(option => optionsMap.set(option.id, option));

  // Initialize an array to store the sorted options
  const sortedOptions = [];

  // Function to recursively add children to the sorted array
  function addChildren (parentId, depth) {
    options
      .filter(option => option.parent === parentId)
      .forEach(option => {
        sortedOptions.push({ ...option, depth });
        addChildren(option.id, depth + 1); // Recursively add children
      });
  }

  // Start by adding top-level items (those with an empty parent)
  addChildren('', 0);

  return sortedOptions;
}

/**
 * WOSettings is a generic settings interface.
 * User can define
 */
export default class WOSettings extends Component {
  constructor (props) {
    super(props);
    this.handleRowEvent = this.handleRowEvent.bind(this);
    this.renderRow = this.renderRow.bind(this);
  }

  handleRowEvent (event, key, type, colorPicker = false) {
    const { setProps, options } = this.props;
    const oldOptions = structuredClone(options);
    const current = oldOptions.find(option => option.id === key);
    if (colorPicker) {
      current.types[type].color = event.target.value;
    } else {
      const { checked } = event.target;
      current.types[type].value = checked;
      current.types[type].color = current.types[type].color || generateNewHighlightColor();
    }
    setProps({ options: oldOptions });
  }

  renderRow (row) {
    const highlightCell = (row.types && 'highlight' in row.types)
      ? (<>
        <input type='checkbox' checked={row.types.highlight.value || false} onChange={(e) => this.handleRowEvent(e, row.id, 'highlight')} />
        {row.types.highlight.value
          ? <input type='color' value={row.types.highlight.color || '#121212'} onChange={(e) => this.handleRowEvent(e, row.id, 'highlight', true)} />
          : null}
      </>)
      : null;
    const metricCell = (row.types && 'metric' in row.types)
      ? <input type='checkbox' checked={row.types.metric.value || false} onChange={(e) => this.handleRowEvent(e, row.id, 'metric')} />
      : null;
    return (
      <tr key={row.id}>
        <td>{'\u00A0'.repeat(row.depth * 2) + row.label}</td>
        <td>{highlightCell}</td>
        {/* <td>{metricCell}</td> */}
      </tr>
    );
  }

  render () {
    const { id, className, options } = this.props;
    const rows = sortOptionsIntoTree(options);
    // TODO due to a HACK with passing data to the child component of
    // the student tiles, we currently only support a single child and
    // expect it to be the highlighted text component.
    return (
      <table
        key={`wo-settings-${id}`}
        className={`WOSettings ${className}`}
        id={id}
      >
        <thead>
          <tr>
            <th>Name</th>
            <th>Highlight</th>
            {/* <th>Metric</th> */}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => this.renderRow(r))}
        </tbody>
      </table>
    );
  }
};

WOSettings.defaultProps = {
  id: '',
  className: '',
  options: {}
};

WOSettings.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,

  /**
   * Array of available options
   */
  options: PropTypes.arrayOf(PropTypes.exact({
    id: PropTypes.string,
    label: PropTypes.string,
    parent: PropTypes.string,
    types: PropTypes.oneOfType([
      PropTypes.object,
      PropTypes.undefined
    ])
  }))

};
