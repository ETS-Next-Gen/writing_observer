import React, { Component } from "react";
import PropTypes from "prop-types";
import Badge from "react-bootstrap/Badge";

/**
 * LOMetrics creates badges for numeric values.
 * It takes a property, `data`, and
 * outputs each item as a badge.
 * If the id of the item is not in the property `shown`,
 * it will not appear.
 */
export default class LOMetrics extends Component {
    constructor(props) {
        super(props);
        this.renderMetricBadge = this.renderMetricBadge.bind(this);
    }
  renderMetricBadge([key, metric]) {
    const { shown } = this.props;

    if (!shown.includes(key)) {
      return null;
    }

    return (
      <Badge key={key} bg="info" pill title={metric.help || metric.value}>
        {metric.value} {metric.label}
      </Badge>
    );
  };
  render() {
    const { id, data, className = '' } = this.props;

    const metricBadges = Object.entries(data).map(this.renderMetricBadge);

    return (
      <div
        key="metric-badges"
        className={`LOMetrics ${className}`}
        id={id}
      >
        {metricBadges}
      </div>
    );
  }
}

LOMetrics.defaultProps = {
  shown: [],
  data: {},
};

LOMetrics.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
     * Data for the metrics should be in form:
     * `{
            "sentences": {
                "id": "sentences",
                "value": 33,
                "label": " sentences"
            },
        }`
     */
  data: PropTypes.object,

  /**
   * Which ids to show.
   */
  shown: PropTypes.array,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,
};
