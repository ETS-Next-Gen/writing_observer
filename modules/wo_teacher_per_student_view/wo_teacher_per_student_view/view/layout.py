'''
Define layout for student dashboard view
'''
import dash_bootstrap_components as dbc

from learning_observer.dash_wrapper import dcc, clientside_callback, Output, Input
import lo_dash_react_components as lodrc
import wo_teacher_per_student_view.view.student_layout as student_layout


prefix = 'teacher-per-student-view'
websocket = f'{prefix}-websocket'
student_select = f'{prefix}-student-select-header'
student_store = f'{prefix}-student-store'
course_store = f'{prefix}-course-store'


def layout():
    """
    """
    layout = dbc.Spinner(
        dbc.Container(
            [
                lodrc.StudentSelectHeader(id=student_select, students=[]),
                lodrc.LOConnection(id=websocket),
                student_layout.student_view,
                dcc.Store(
                    id=student_store,
                    data=[]
                ),
                dcc.Store(
                    id=course_store,
                    data=None
                )
            ]
        ),
        color='primary'
    )
    return layout


clientside_callback(
    '''
    function(url_hash) {
        if (url_hash.length === 0) {return window.dash_clientside.no_update;}
        const decoded = decode_string_dict(url_hash.slice(1));
        return decoded.course_id;
    }
    ''',
    Output(course_store, 'data'),
    Input('_pages_location', 'hash')
)

clientside_callback(
    """
    function(course) {
        const ret = {"module": "latest_data", "course": course};
        return ret;
    }
    """,
    Output(websocket, 'data_scope'),
    Input(course_store, 'data')
)

clientside_callback(
    '''
    async function(course_id) {
        console.log(course_id);
        const response = await fetch(`${window.location.protocol}//${window.location.hostname}:${window.location.port}/webapi/courseroster/${course_id}`);
        const data = await response.json();
        return data.map(function(d) { return d.profile.name.full_name; });
    }
    ''',
    Output(student_store, 'data'),
    Input(course_store, 'data')
)

clientside_callback(
    '''
    function(students) {
        return [students, students[0]];
    }
    ''',
    Output(student_select, 'students'),
    Output(student_select, 'selectedStudent'),
    Input(student_store, 'data')
)

clientside_callback(
    '''
    function(student) {
        return student;
    }
    ''',
    Output(student_layout.name, 'children'),
    Input(student_select, 'selectedStudent')
)


clientside_callback(
    '''
    function(msg, student) {
        const data = JSON.parse(msg.data);
        const curr_student_index = data.latest_writing_data.findIndex(s => s.student.profile.name.full_name === student);
        const student_data = data.latest_writing_data[curr_student_index];
        // console.log(student, curr_student_index, student_data);
        const sentence_type_data = JSON.parse(student_data?.sentence_types?.metric ?? "{}");
        const sentence_type_labels = Object.keys(sentence_type_data);
        const sentence_type_values = Object.values(sentence_type_data);
        const highlight = {
            testHighlight: {
                id: "testHighlight",
                value: [
                    [5, 7],
                    [19, 28],
                ],
                label: "Test Highlight",
            },
        };
        return [student_data?.text ?? "", highlight, [{values: [sentence_type_values], labels: [sentence_type_labels]}, [0], sentence_type_values.length]];
    }
    ''',
    Output(student_layout.highlight, 'text'),
    Output(student_layout.highlight, 'highlight_breakpoints'),
    Output(student_layout.pie_chart, 'extendData'),
    Input(websocket, 'message'),
    Input(student_select, 'selectedStudent')
)

clientside_callback(
    '''
    function(student) {
        return [JSON.stringify(['sentence_types'])];
    }
    ''',
    Output(websocket, 'send'),
    Input(student_select, 'selectedStudent')
)
