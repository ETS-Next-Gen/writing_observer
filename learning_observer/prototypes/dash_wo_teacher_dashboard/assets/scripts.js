if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.minty_colors = ['#78c2ad', '#f3969a', '#6cc3d5', '#ffce67', '#ff7851']
window.dash_clientside.clientside = {

    change_sort_direction_icon: function(values, sort_values) {
        if (sort_values.length == 0) {
            return ['fas fa-sort', 'None']
        }
        if (values.includes('checked')) {
            return ['fas fa-sort-down', 'Desc']
        }
        return ['fas fa-sort-up', 'Asc']
    },

    reset_sort_options: function(clicks) {
        if (clicks) {
            return [];
        }
        return window.dash_clientside.no_update;
    },

    sort_students: function(values, direction, data, options, students) {
        let orders = Array(students).fill(window.dash_clientside.no_update);
        if (values.length === 0) {
            // preserves current order when no values are present
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
        if (!msg) {
            return old_data;
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data);
        for (const up of data) {
            let index = up.id;
            updates[index] = {...old_data[index], ...up};
            updates[index] = _.merge(old_data[index], up);
        }
        return updates;
    },

    open_offcanvas: function(clicks, close, is_open, students) {
        const trig = dash_clientside.callback_context.triggered[0];
        if(!is_open & (typeof trig !== 'undefined')) {
            if (trig.prop_id === 'teacher-dashboard-settings-show-hide-open-button.n_clicks') {
                return [true, Array(students).fill('col-12 col-lg-6 col-xxl-4'), 'col-xxl-9 col-lg-8 col-md-6'];
            }
        }
        return [false, Array(students).fill('col-12 col-md-6 col-lg-4 col-xxl-3'), ''];
    },

    toggle_open_close: function(value, is_open) {
        if (value) {
            return !is_open;
        }
        return is_open;
    },

    // TODO there is probably a better way to handle the following functions
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
        const l = values.concat(metrics).concat(text).concat(highlights).concat(indicators);
        return Array(students).fill(l);
    },

    send_websocket: function (reports, student) {
        if (typeof student === "undefined") {
            return window.dash_clientside.no_update;
        }
        const msg = {"reports":reports, "student":student};
        return JSON.stringify(msg);
    }
}
