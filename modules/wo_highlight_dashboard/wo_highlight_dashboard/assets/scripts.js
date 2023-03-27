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
        if (sort_check.includes('checked')) {
            return ['fas fa-sort-down', 'Desc'];
        }
        return ['fas fa-sort-up', 'Asc'];
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

    sort_students: function(values, direction, data, student_ids, options, students) {
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
        // Input({'type': student_indicators, 'index': ALL}, 'data'),
        // State(student_store, 'data'),
        // State(settings.sort_by_checklist, 'options'),
        // State(student_counter, 'data')

        let orders = Array(students).fill(window.dash_clientside.no_update);
        if (values.length === 0) {
            // default sort is alphabetical by student id
            const sort_order = [...student_ids.keys()].sort((a, b) => student_ids[a].id - student_ids[b].id);
            orders = sort_order.map(idx => {return {'order': (direction.includes('checked') ? student_ids.length - idx : idx)}});
            return orders;
        }
        let labels = options.map(obj => {return (values.includes(obj.value) ? obj.label : '')});
        labels = labels.filter(e => e);
        for (let i = 0; i < data.length; i++) {
            let score = 0;
            values.forEach(function (item, index) {
                score += data[i][`${item}_indicator`]['value'];
            });
            let order = (direction.includes('checked') ? (100*values.length) - score : score);
            orders[i] = {'order': order};
        }
        return orders;
    },

    populate_student_data: function(msg, student_ids, prev_metrics, prev_text, prev_highlights, prev_indicators, students, msg_count) {
        // Populates and updates students data from the websocket
        // for each update, parse the data into the proper format
        // Also return the current time
        //
        // Output({'type': student_metrics, 'index': ALL}, 'data'),
        // Output({'type': student_texthighlight, 'index': ALL}, 'text'),
        // Output({'type': student_texthighlight, 'index': ALL}, 'highlight_breakpoints'),
        // Output({'type': student_indicators, 'index': ALL}, 'data'),
        // Output({'type': student_link, 'index': ALL}, 'href'),
        // Output(last_updated, 'children'),
        // Output(msg_counter, 'data'),
        // Input(websocket, 'message'),
        // State(student_store, 'data'),
        // State({'type': student_metrics, 'index': ALL}, 'data'),
        // State({'type': student_texthighlight, 'index': ALL}, 'text'),
        // State({'type': student_texthighlight, 'index': ALL}, 'highlight_breakpoints'),
        // State({'type': student_indicators, 'index': ALL}, 'data'),
        // State(student_counter, 'data')
        if (!msg) {
            return [prev_metrics, prev_text, prev_highlights, prev_indicators, -1, 0];
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data)['latest_writing_data'];
        // console.log(data);
        for (let i = 0; i < data.length; i++) {
            let curr_user = data[i].student.user_id;
            let user_index = student_ids.findIndex(item => item.user_id === curr_user)
            const last_document = data[i]?.student?.['writing_observer.writing_analysis.last_document'];
            updates[user_index] = {
                'id': curr_user,
                'text': {
                    "student_text": {
                        "id": "student_text",
                        "value": data[i].text,
                        "label": "Student text"
                    }
                },
                'highlight': {},
                'metrics': {},
                'indicators': {},
                'link': last_document ? `https://docs.google.com/document/d/${last_document.document_id}/edit` : ''
            }
            for (const key in data[i]) {
                let item = data[i][key];
                const sum_type = (item.hasOwnProperty('summary_type') ? item['summary_type'] : '');
                // we set each id to be ${key}_{type} so we can select items by class name when highlighting
                if (sum_type === 'total') {
                    updates[user_index]['metrics'][`${key}_metric`] = {
                        'id': `${key}_metric`,
                        'value': item['metric'],
                        'label': item['label']
                    }
                } else if (sum_type === 'percent') {
                    updates[user_index]['indicators'][`${key}_indicator`] = {
                        'id': `${key}_indicator`,
                        'value': item['metric'],
                        'label': item['label']
                    }
                }
                const offsets = (item.hasOwnProperty('offsets') ? item['offsets'] : '');
                if (offsets.length !== 0) {
                    updates[user_index]['highlight'][`${key}_highlight`] = {
                        'id': `${key}_highlight`,
                        'value': item['offsets'],
                        'label': item['label']
                    }
                }
            }
        }
        const timestamp = new Date();

        // return the data to each each module
        return [
            updates.map(function(d) { return d['metrics']; }), // metrics
            updates.map(function(d) { return d['text']['student_text']['value']; }), // texthighlight text
            updates.map(function(d) { return d['highlight']; }), // texthighlight highlighting
            updates.map(function(d) { return d['indicators']; }), // indicators
            updates.map(function(d) { return d['link']; }), // student doc links
            timestamp, // current time
            msg_count + 1 // set message count
        ];
    },
    
    update_last_updated_text: function(last_time, intervals) {
        // Whenever we get a new message or 5 seconds have passed, update the last updated text

        // Output(last_updated_msg, 'children'),
        // Input(last_updated, 'data'),
        // Input(last_updated_interval, 'n_intervals')
        if (last_time === -1) {
            return 'Never';
        }
        const curr_time = new Date();
        const sec_diff = (curr_time.getTime() - last_time.getTime())/1000
        if (sec_diff < 1) {
            return 'just now'
        }
        const ms_since_last_message = rendertime2(sec_diff);
        return `${ms_since_last_message} ago`;
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

    fetch_nlp_options: async function(trigger) {
        // Fetch possible NLP options from the server to later build the settings panel
        //
        // Output(nlp_options, 'data'),
        // Input(prefix, 'className')
        const response = await fetch(`${window.location.protocol}//${window.location.hostname}:${window.location.port}/views/writing_observer/nlp-options/`);
        const data = await response.json();
        return data;
    },

    update_course_assignment: function(url_hash) {
        // Update the course and assignment info based on the hash query string
        //
        // Output(course_store, 'data'),
        // Output(assignment_store, 'data'),
        // Input('_pages_location', 'hash')
        if (url_hash.length === 0) {return window.dash_clientside.no_update;}
        const decoded = decode_string_dict(url_hash.slice(1))
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
            // Mints primary 4 colors with a 0.25 opacity
            // 'rgba(86, 204, 157, 0.25)', 'rgba(108, 195, 213, 0.25)',
            // 'rgba(255, 206, 103, 0.25)', 'rgba(255, 120, 81, 0.25)',
            // Plotly's T10 with a 0.25 opacity applied
            'rgba(245, 133, 24, 0.25)',
            'rgba(114, 183, 178, 0.25)', 'rgba(228, 87, 86, 0.25)', 
            'rgba(84, 162, 75, 0.25)', 'rgba(238, 202, 59, 0.25)',
            'rgba(178, 121, 162, 0.25)', 'rgba(255, 157, 166, 0.25)',
            'rgba(76, 120, 168, 0.25)', 
        ];
        let docs = [];
        const shown_colors = {};
        // remove all highlighting and record current colors
        options.forEach(item => {
            docs = document.getElementsByClassName(`${item.value}_highlight`);
            if (docs.length === 0) {return window.dash_clientside.no_update;}
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
                    // console.log(dc, hc, combined);
                    docs[i].style.backgroundColor = combined;
                } else {
                    docs[i].style.backgroundColor = high_color;
                }
            }
        })
    },

    set_status: function(status) {
        // Set the websocket status icon/title
        //
        // Output(websocket_status, 'className'),
        // Output(websocket_status, 'title'),
        // Input(websocket, 'state')
        if (status === undefined) {
            return window.dash_clientside.no_update;
        }
        const icons = ['fas fa-sync-alt', 'fas fa-check text-success', 'fas fa-sync-alt', 'fas fa-times text-danger'];
        const titles = ['Connecting to server', 'Connected to server', 'Closing connection', 'Disconnected from server'];
        return [icons[status.readyState], titles[status.readyState]];
    },

    show_hide_initialize_message: function(msg_count) {
        // Show or hide the initialization message based on how many messages we've seen
        //
        // Output(initialize_alert, 'is_open'),
        // Input(msg_counter, 'data')
        if (msg_count > 0){
            return false;
        }
        return true;
    },

    send_options_to_server: function(types, metrics, highlights, indicators, sort_by) {
        // Send selected options to the server 
        // TODO work on protocol for communicating with the 
        //
        // Output(websocket, 'send'),
        // Input(settings.checklist, 'value'),
        // Input(settings.metric_checklist, 'value'),
        // Input(settings.highlight_checklist, 'value'),
        // Input(settings.indicator_checklist, 'value')
        // Input(settings.sort_by_checklist, 'value')
        const data = metrics.concat(highlights).concat(indicators).concat(sort_by);
        return [JSON.stringify(data)]
    },

    show_nlp_running_alert: function(msg_count, checklist, metrics, highlight, indicator, sort_by) {
        // Show or hide the NLP running alert
        // On new selections, show alert.
        // When new data comes in, hide the alert
        //
        // Output({'type': alert_type, 'index': nlp_running_alert}, 'is_open'),
        // Input(msg_counter, 'data'),
        // Input(settings.checklist, 'value'),
        // Input(settings.metric_checklist, 'value'),
        // Input(settings.highlight_checklist, 'value'),
        // Input(settings.indicator_checklist, 'value'),
        // Input(settings.sort_by_checklist, 'value'),
        const trig = dash_clientside.callback_context.triggered[0];
        if (trig.prop_id === 'teacher-dashboard-msg-counter.data') {
            return false;
        }
        return true;
    },

    update_overall_alert: function(is_open, children) {
        // Update the overall alert system,
        // if only 1 alert exists, show its message,
        // otherwise combine
        //
        // Output(overall_alert, 'label'),
        // Output(overall_alert, 'class_name'),
        // Input({'type': alert_type, 'index': ALL}, 'is_open'),
        // Input({'type': alert_type, 'index': ALL}, 'children'),
        const truth = is_open.filter(function(e) {return e}).length;
        if (truth == 1) {
            return [children[is_open.indexOf(true)], '']
        }
        if (truth > 1) {
            return [`Waiting on ${truth} items to finish`, ''];
        }
        return [window.dash_clientside.no_update, 'hidden-alert'];
    }
}
