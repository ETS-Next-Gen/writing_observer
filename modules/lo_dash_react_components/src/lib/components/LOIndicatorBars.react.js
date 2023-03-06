import React, {Component} from 'react';
import PropTypes from 'prop-types';
import ProgressBar from 'react-bootstrap/ProgressBar';

/**
 * LOIndicatorBars provide progress bars.
 * It takes a property, `data`, and
 * outputs each item as a label/progress bar pair.
 * If the id of the item is not in the property `shown`,
 * it will not appear.
 */
export default class LOIndicatorBars extends Component {

    render() {
        const {id, data, shown, className} = this.props;

        // Map colors to ranges: 0-33 (danger), 34-67 (warning, and 68-100 (success)
        const indicator_colors = ['danger', 'warning', 'success'];
        const INDICATOR_STEP = 34;

        const indicator_bars = Object.entries(data).map(([key, indicator]) => {
            return (
                <div
                    key={key}
                    className={shown.includes(indicator.id) ? 'd-table-row': 'd-none'}
                >
                    <div key='indicator-text' className='small d-table-cell text-nowrap'>
                        {indicator.label}:
                    </div>
                    <div
                        className='d-table-cell w-100 align-middle '
                    >
                        <ProgressBar
                            key='indicator-bar'
                            now={indicator.value}
                            title={`${indicator.value}% ${indicator.help}`}
                            variant={indicator_colors[Math.floor((indicator.value) / INDICATOR_STEP)]}
                        />
                    </div>
                </div>
            )
        })

        return (
            <div
                key='indicator-bars'
                className={`${className} d-table`}
                id={id}
            >
                {indicator_bars}
            </div>
        );
    }
}

LOIndicatorBars.defaultProps = {
    shown: [],
    data: {}
};

LOIndicatorBars.propTypes = {
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
            "transitions": {
                "id": "transitions",
                "value": 81,
                "label": "Transitions",
                "help": "Percentile based on total number of transitions used"
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
    setProps: PropTypes.func
};
