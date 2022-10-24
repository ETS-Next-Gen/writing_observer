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
        // for each update, merge in new data

        // Output({'type': student_card, 'index': ALL}, 'data'),
        // Input(websocket, 'message'),
        // State({'type': student_card, 'index': ALL}, 'data'),
        // State(student_counter, 'data')

        if (!msg) {
            return [old_data, 'Never'];
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data)['student-data'];
        console.log(msg)
        for (let i = 0; i < students; i++) {
            updates[i] = {
                'id': data[i].userId,
                'text': {
                    "studenttext": {
                        "id": "studenttext",
                        "value": data[i].writing_observer_compiled.text,
                        "label": "Student text"
                    }
                },
                'highlight': {},
                'metrics': {
                    "timeontask": {
                        "id": "timeontask",
                        "value": rendertime2(data[i]['writing_observer.writing_analysis.time_on_task'].total_time_on_task),
                        "label": " on task"
                    },
                },
                'indicators': {}
            }
        }
        return [updates, msg.timeStamp];
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
        // Input(settings.show_hide_settings_open, 'n_clicks'),
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
    
    // Output(show_hide_settings_indicator_collapse, 'is_open'),
    // Input(show_hide_settings_checklist, 'value')
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
        // Input(settings.show_hide_settings_checklist, 'value'),
        // Input(settings.show_hide_settings_metric_checklist, 'value'),
        // Input(settings.show_hide_settings_text_radioitems, 'value'),
        // Input(settings.show_hide_settings_highlight_checklist, 'value'),
        // Input(settings.show_hide_settings_indicator_checklist, 'value'),
        // State(student_counter, 'data')
        const l = values.concat(metrics).concat(text).concat(highlights).concat(indicators);
        return Array(students).fill(l);
    },
}
