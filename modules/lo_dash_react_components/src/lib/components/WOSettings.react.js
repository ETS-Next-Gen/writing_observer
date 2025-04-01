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
  const optionsMap = new Map();
  options.forEach(option => optionsMap.set(option.id, option));

  const sortedOptions = [];

  function addChildren (parentId, depth) {
    options
      .filter(option => option.parent === parentId)
      .forEach(option => {
        sortedOptions.push({ ...option, depth });
        addChildren(option.id, depth + 1);
      });
  }

  addChildren('', 0);

  return sortedOptions;
}

export default class WOSettings extends Component {
  constructor (props) {
    super(props);
    this.state = {
      collapsed: {} // Tracks which rows are collapsed
    };
    this.handleRowEvent = this.handleRowEvent.bind(this);
    this.renderRow = this.renderRow.bind(this);
    this.toggleCollapse = this.toggleCollapse.bind(this);
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

  toggleCollapse (id) {
    this.setState(prevState => ({
      collapsed: {
        ...prevState.collapsed,
        [id]: !prevState.collapsed[id]
      }
    }));
  }

  renderRow (row, allRows) {
    const { collapsed } = this.state;
    const hasChildren = allRows.some(option => option.parent === row.id);
    const isCollapsed = collapsed[row.id] || false;

    const highlightCell = row.types && 'highlight' in row.types
      ? (<>
        <input
          type="checkbox"
          checked={row.types.highlight.value || false}
          onChange={(e) => this.handleRowEvent(e, row.id, 'highlight')}
        />
        {row.types.highlight.value
          ? (<input
            type="color"
            value={row.types.highlight.color || '#121212'}
            onChange={(e) => this.handleRowEvent(e, row.id, 'highlight', true)}
          />)
          : null}
      </>)
      : null;

    return (
      <>
        <tr key={row.id}>
          <td >
            <div style={{
              display: 'inline-block',
              paddingLeft: `${row.depth}em`
            }}>{row.label}</div>
            {hasChildren && (
              <button
                onClick={() => this.toggleCollapse(row.id)}
                style={{
                  marginLeft: '4px',
                  cursor: 'pointer',
                  background: 'none',
                  border: 'none'
                }}
              >
                {isCollapsed ? '▶' : '▼'}
              </button>
            )}
          </td>
          <td>{highlightCell}</td>
        </tr>
        {/* Render children rows if not collapsed */}
        {!isCollapsed &&
          allRows
            .filter(child => child.parent === row.id)
            .map(child => this.renderRow(child, allRows))}
      </>
    );
  }

  render () {
    const { id, className, options } = this.props;
    const rows = sortOptionsIntoTree(options);

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
          </tr>
        </thead>
        <tbody>
          {rows
            .filter(row => row.parent === '') // Start with top-level rows
            .map(row => this.renderRow(row, rows))}
        </tbody>
      </table>
    );
  }
}

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
