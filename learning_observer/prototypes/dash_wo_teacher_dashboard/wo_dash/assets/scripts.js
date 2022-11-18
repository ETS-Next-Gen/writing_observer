/*
    Javascript functions
    This file contains Javascript functions that will be
    called through a clientside callback in the Python code.
    An example of how to run the javascript function, see below

    Essentially its just a JSON that defines functions.

    You'll see `window.dash_clientside.no_update` appear often in the code.
    This tells dash not to update the output component.
    If we don't need to update it, we shouldn't!
    
    This is often used with initializing the array of students to return.
    `Array(students).fill(window.dash_clientside.no_update);`
    Where `students` is the total number of students
*/
// initialize dash_clientside
if (!window.dash_clientside) {
    window.dash_clientside = {};
}

function getRGBAValues(str) {
    var vals = str.substring(str.indexOf('(') +1, str.length -1).split(', ');
    return {
        'r': parseInt(vals[0]),
        'g': parseInt(vals[1]),
        'b': parseInt(vals[2]),
        'o': parseFloat(vals[3])
    };
}

// define functions we are calling
window.dash_clientside.clientside = {

    change_sort_direction_icon: function(sort_check, sort_values) {
        // updates UI elements, does not handle sorting
        // based on the current sort, set the sort direction icon and sort text

        // Output(sort_icon, 'className'),
        // Output(sort_label, 'children'),
        // Input(sort_toggle, 'value'),
        // Input(sort_by_checklist, 'value')
        if (sort_values.length == 0) {
            return ['fas fa-sort', 'None']
        }
        if (sort_check.includes('checked')) {
            return ['fas fa-sort-down', 'Desc']
        }
        return ['fas fa-sort-up', 'Asc']
    },

    reset_sort_options: function(clicks) {
        // resets the sort_by_checklist, this will trigger sort_students and change_sort_direction_icon

        // Output(sort_by_checklist, 'value'),
        // Input(sort_reset, 'n_clicks')
        if (clicks) {
            return [];
        }
        return window.dash_clientside.no_update;
    },

    sort_students: function(values, direction, data, options, students) {
        // We sort students whenever one of the following occurs:
        // 1. the checklist for sorting changes
        // 2. the direction of sorting changes
        // 3. the student's data changes
        // We add the value of each indicator checked in the checklist to determine score for each student
        // We then set the order style attribute of each student to their score
        // Items with order=1 come before items with order=2 and so on.
        // This will set students in ascending order (low scoring students first)
        // We set a max and subtract from it to determine descending order (high scoring students first)

        // Output({'type': student_col, 'index': ALL}, 'style'),
        // Input(settings.sort_by_checklist, 'value'),
        // Input(settings.sort_toggle, 'value'),
        // Input({'type': student_card, 'index': ALL}, 'data'),
        // State(settings.sort_by_checklist, 'options'),
        // State(student_counter, 'data')

        // TODO fix sorting, haven't been updated with the new NLP data
        let orders = Array(students).fill(window.dash_clientside.no_update);
        if (values.length === 0) {
            // preserves current order when no values are present
            // TODO determine some default ordering instead of leaving it as is
            return orders
        }
        let labels = options.map(obj => {return (values.includes(obj.value) ? obj.label : '')});
        labels = labels.filter(e => e);
        for (let i = 0; i < data.length; i++) {
            let score = 0;
            values.forEach(function (item, index) {
                score += data[i].indicators[item]['value'];
            });
            let order = (direction.includes('checked') ? (100*values.length) - score : score);
            orders[i] = {'order': order};
        }
        return orders;
    },

    populate_student_data: function(msg, old_data, students) {
        // Populates and updates students data from the websocket
        // for each update, parse the data into the proper format
        // Also return the current time
        //
        // Output({'type': student_card, 'index': ALL}, 'data'),
        // Output(last_updated, 'children'),
        // Input(websocket, 'message'),
        // State({'type': student_card, 'index': ALL}, 'data'),
        // State(student_counter, 'data')

        if (!msg) {
            return [old_data, 'Never']; //, 0, []];
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data)['latest_writing_data'];
        const stud_data = data.map(x => x.student);
        // console.log(data);
        for (let i = 0; i < data.length; i++) {
            // TODO whatever data is included in the message should be parsed into it's appropriate spot
            updates[i] = {
                'id': data[i].userId,
                'text': {
                    "student_text": {
                        "id": "student_text",
                        "value": data[i].text,
                        "label": "Student text"
                    }
                },
                'highlight': {},
                'metrics': {},
                'indicators': {}
            }
            for (const key in data[i]) {
                let item = data[i][key];
                const sum_type = (item.hasOwnProperty('summary_type') ? item['summary_type'] : '');
                if (sum_type === 'total') {
                    updates[i]['metrics'][`${key}_metric`] = {
                        'id': `${key}_metric`,
                        'value': item['metric'],
                        'label': item['label']
                    }
                } else if (sum_type === 'percent') {
                    updates[i]['indicators'][`${key}_indicator`] = {
                        'id': `${key}_indicator`,
                        'value': item['metric'],
                        'label': item['label']
                    }
                }
                const offsets = (item.hasOwnProperty('offsets') ? item['offsets'] : '');
                if (offsets.length !== 0) {
                    updates[i]['highlight'][`${key}_highlight`] = {
                        'id': `${key}_highlight`,
                        'value': item['offsets'],
                        'label': item['label']
                    }
                }
            }
        }
        const timestamp = new Date();

        const count = (data.length == students ? window.dash_clientside.no_update : data.length)
        const new_students = (stud_data.length == students ? window.dash_clientside.no_update : stud_data)

        return [updates, timestamp.toLocaleTimeString()]; //, count, new_students];
    },

    open_settings: function(clicks, close, is_open, students) {
        // Toggles the settings panel
        // Based on if its open or not, we adjust the grid css classes of students and the panel itself
        // this makes the student card remain the same size even if the settings panel is open.
        //
        // There are multiple ways to close the settings button (x button or click settings again).
        // This means we have to determine which input fired and handle the possible cases.

        // Output(settings_collapse, 'is_open'),
        // Output({'type': student_col, 'index': ALL}, 'class_name'),
        // Output(student_grid, 'class_name'),
        // Input(settings.open_btn, 'n_clicks'),
        // Input(settings.close_settings, 'n_clicks'),
        // State(settings_collapse, 'is_open'),
        // State(student_counter, 'data')

        // determine which button caused this callback to trigger
        const trig = dash_clientside.callback_context.triggered[0];
        if(!is_open & (typeof trig !== 'undefined')) {
            if (trig.prop_id === 'teacher-dashboard-settings-show-hide-open-button.n_clicks') {
                return [true, Array(students).fill('col-12 col-lg-6 col-xxl-4'), 'col-xxl-9 col-lg-8 col-md-6'];
            }
        }
        return [false, Array(students).fill('col-12 col-md-6 col-lg-4 col-xxl-3'), ''];
    },

    // TODO there is probably a better way to handle the following functions
    // The following functions all do the same thing but with different values
    // On the settings panel, they show or hide the sub-options for each option based on if the option is checked or not.
    // Indicators options are shown vs. not
    // [x] Indicators           ->  [] Indicators
    //     [x] Transitions      ->
    //     [] Other             ->
    
    // Output(indicator_collapse, 'is_open'),
    // Input(checklist, 'value')
    toggle_indicators_checklist: function(values) {
        if (values.includes('indicators')) {
            return true;
        }
        return false;
    },

    toggle_metrics_checklist: function(values) {
        if (values.includes('metrics')) {
            return true;
        }
        return false;
    },

    toggle_text_checklist: function(values) {
        if (values.includes('text')) {
            return true;
        }
        return false;
    },

    toggle_highlight_checklist: function(values) {
        if (values.includes('highlight')) {
            return true;
        }
        return false;
    },

    show_hide_data: function(values, metrics, text, highlights, indicators, students) {
        // Change which items appear on the student cards
        // The student card will only show elements whose id is in the `shown` property.
        // Ids not included will not be shown
        // 
        // All settings checklists/radioitems are combined into a single list and passed to all student cards
        //
        // Output({'type': student_card, 'index': ALL}, 'shown'),
        // Input(settings.checklist, 'value'),
        // Input(settings.metric_checklist, 'value'),
        // Input(settings.text_radioitems, 'value'),
        // Input(settings.highlight_checklist, 'value'),
        // Input(settings.indicator_checklist, 'value'),
        // State(student_counter, 'data')
        const l = values.concat(metrics.map(x => `${x}_metric`))
            .concat(text)
            .concat(highlights.map(x => `${x}_highlight`))
            .concat(indicators.map(x => `${x}_indicator`));
        return Array(students).fill(l);
    },

    update_students: async function(course_id) {
        // Fetch the student information based on course id

        // Output(student_counter, 'data'),
        // Output(student_store, 'data'),
        // Input(course_store, 'data')
        const response = await fetch(`${window.location.protocol}//${window.location.hostname}:${window.location.port}/webapi/courseroster/${course_id}`);
        const data = await response.json();
        return [data.length, data];
    },

    fetch_assignment_info: async function(course_id, assignment_id) {
        // Fetch assignment information from server based on course and assignment id
        // Not yet implemented, TODO
        //
        // Output(assignment_name, 'children'),
        // Output(assignment_desc, 'children'),
        // Input(course_store, 'data'),
        // Input(assignment_store, 'data')
        return [`Assignment ${assignment_id}`, `This is assignment ${assignment_id} from course ${course_id}`]
    },

    update_course_assignment: function(hash) {
        // Update the course and assignment info based on the hash query string
        //
        // Output(course_store, 'data'),
        // Output(assignment_store, 'data'),
        // Input('_pages_location', 'hash')
        if (hash.length === 0) {return window.dash_clientside.no_update;}
        const decoded = decode_string_dict(hash.slice(1))
        return [decoded.course_id, decoded.assignment_id]
    },

    highlight_text: function(overall_show, shown, data_trigger, options) {
        // Highlights the text appropriately
        //
        // Output(settings.dummy, 'style'),
        // Input(settings.checklist, 'value'),
        // Input(settings.highlight_checklist, 'value'),
        // Input({'type': student_card, 'index': ALL}, 'data'),
        // State(settings.highlight_checklist, 'options')

        if (!overall_show.includes('highlight')) {return window.dash_clientside.no_update;}
        const colors = [
            'rgba(86, 204, 157, 0.25)', 'rgba(108, 195, 213, 0.25)',
            'rgba(255, 206, 103, 0.25)', 'rgba(255, 120, 81, 0.25)'
        ];
        let docs = [];
        const shown_colors = {};
        // remove all highlighting and record current colors
        options.forEach(item => {
            docs = document.getElementsByClassName(`${item.value}_highlight`);
            if (shown.includes(item.value)) {
                if (docs[0].style.backgroundColor.length > 0 & docs[0].style.backgroundColor !== 'transparent') {
                    shown_colors[item.value] = docs[0].style.backgroundColor;
                }
            }
            for (var i = 0; i < docs.length; i++) {
                docs[i].style.backgroundColor = 'transparent';
            }
        })
        // highlight shown items
        let high_color = '';
        shown.forEach(item => {
            docs = document.getElementsByClassName(`${item}_highlight`);
            // fetch current color or figure out a new one
            if (shown_colors.hasOwnProperty(item)) {
                high_color = shown_colors[item];
            } else {
                let curr_colors = Object.values(shown_colors);
                let remaining_colors = Array.from(new Set([...colors].filter(x => !curr_colors.includes(x))));
                high_color = (remaining_colors.length === 0 ? colors[Math.floor(Math.random()*colors.length)] : remaining_colors[0])
                shown_colors[item] = high_color;
            }

            // add background color to highlighted elements
            for (var i = 0; i < docs.length; i++) {
                if (docs[i].style.backgroundColor.length > 0 & docs[i].style.backgroundColor !== 'transparent') {
                    let dc = getRGBAValues(docs[i].style.backgroundColor);
                    let hc = getRGBAValues(high_color);
                    let combined = `rgba(${parseInt((dc.r+hc.r)/2)}, ${parseInt((dc.g+hc.g)/2)}, ${parseInt((dc.b+hc.b)/2)}, ${hc.o+dc.o})`;
                    console.log(dc, hc, combined);
                    docs[i].style.backgroundColor = combined;
                } else {
                    docs[i].style.backgroundColor = high_color;
                }
            }
        })
    }
}
