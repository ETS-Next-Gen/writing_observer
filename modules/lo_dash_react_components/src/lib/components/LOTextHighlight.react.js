import React, {Component} from 'react';
import PropTypes from 'prop-types';

/**
 * LOTextHighlight provides breakpoints and classes to allow for later highlighting.
 * It takes a property, `text`, and
 * and breaks it up based on all possible breakpoints in property `highlight_breakpoints`.
 * The text is output as a variety of spans with classnames corresponding to ids.
 */
export default class LOTextHighlight extends Component {

    render() {
        const {id, text, highlight_breakpoints, class_name} = this.props;


        // determine the text highlights we want and put them in ascending order
        const highlights = [];
        const breakpoints_set = new Set();
        breakpoints_set.add(0);

        // Iterate over all highlight offsets and add each possible start/end
        // index to a set `breakpoints_set`
        // Also add the start, end, and id to highlights
        for (const [key, value] of Object.entries(highlight_breakpoints)) {
            for (const values of value.value) {
                breakpoints_set.add(values[0]);
                breakpoints_set.add(values[0]+values[1]);
                highlights.push([values[0], values[0]+values[1], key])
            }
        }
        // Sort highlights and breakpoints by index in ascending order
        highlights.sort((a, b) => a[0] - b[0]);
        const breakpoints = Array.from(breakpoints_set).sort(function(a, b){return a - b});

        // prep text data
        let child = text;
        if (highlights.length > 0) {
            child = new Array();
            let text_slice = '';
            let start = 0;
            let end = 0;
            let classes = [];
            // Iterate over all possible breakpoints to build spans for highlighting
            // 1. Slice text from start to end
            // 2. Add a class for each possible highlight item (reduce)
            // 3. Add span with text and classes to `child`
            for (let i = 0; i < breakpoints.length; i++) {
                start = breakpoints[i];
                end = (i === breakpoints.length-1 ? text.length : breakpoints[i+1]);
                text_slice = text.slice(start, end);
                classes = highlights.reduce((acc, [s, e, c]) => {
                    if (s <= start && e >= end) {
                        acc.push(c);
                    }
                    return acc;
                }, [])
                // spans will auto clip extra whitespace including new lines
                // so we have to split the text on new lines then add in a <br/>
                // on the final split of new lines, we do NOT add the <br/>
                const text_newline_split = text_slice.split('\n');
                child.push(
                    <span
                        key={`text-${start}-${end}`}
                        className={classes.join(' ')}
                    >
                        {text_newline_split.length === 1 ? text_slice : text_newline_split.map((line, i) => (
                            <span key={i}>
                                {line}
                                {i === text_newline_split.length-1 ? '' : <br/>}
                            </span>
                        ))}
                    </span>
                )
            }
        }
        return (
            <div
                key='text-highlight'
                className={class_name || ''}
                id={id}
            >
                {child}
            </div>
        );
    }
}

LOTextHighlight.defaultProps = {
    text: '',
    highlight_breakpoints: {}
};

LOTextHighlight.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Classes for the outer most div.
     */
    class_name: PropTypes.string,

    /**
     * The text to be highlighted.
     */
    text: PropTypes.string,

    /**
     * highlight breakpoints in the form of:
     * `{
            "coresentences": {
                "id": "coresentences",
                "value": [
                    [
                        0,
                        13
                    ],
                    [
                        20,
                        25
                    ]
                ],
                "label": "Main ideas"
            },
        }`
     * 
     */
    highlight_breakpoints: PropTypes.object,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func
};
