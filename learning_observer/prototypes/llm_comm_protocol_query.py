# TODO imports are probably broken, just wanted to
# split this piece into a different file
import llm_pipeline

# Start of real tools
def generate_communication_protocol_query(module=None, goal=None, reducers=None):
    '''Call the llm to generate the communication protocol
    '''
    print('\n*** Starting restaurant booking sub-agent')
    if reducers is None:
        reducers = '```python\nREDUCERS = []\n```'

    agent = llm_pipeline.create_llm_messager(
        system_template=None,
        messages_template=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "<examples>\n<example>\n<goal>\nFetch the latest submission for each student in the course, calculate its code complexity, and join this information with the student roster to provide a comprehensive view of current student performance.\n</goal>\n<module>\ncoding_analyzer\n</module>\n<reducers>\n```python\nREDUCERS = [\n    {\n        'context': \"org.learning-observer.coding.programming_skills\",\n        'scope': coding_analyzer.student_scope,\n        'function': coding_analyzer.code_complexity,\n        'default': {'complexity_score': 0}\n    },\n    {\n        'context': \"org.learning-observer.coding.programming_skills\",\n        'scope': coding_analyzer.assignment_scope,\n        'function': coding_analyzer.submission_count,\n        'default': {'submissions': 0}\n    },\n    {\n        'context': \"org.learning-observer.coding.programming_skills\",\n        'scope': coding_analyzer.student_scope,\n        'function': coding_analyzer.language_usage,\n        'default': {'languages': {}}\n    },\n    {\n        'context': \"org.learning-observer.coding.programming_skills\",\n        'scope': coding_analyzer.assignment_scope,\n        'function': coding_analyzer.test_case_results,\n        'default': {'passed': 0, 'failed': 0}\n    },\n    {\n        'context': \"org.learning-observer.coding.programming_skills\",\n        'scope': coding_analyzer.student_scope,\n        'function': coding_analyzer.time_to_completion,\n        'default': {'average_time': 0}\n    },\n    {\n        'context': \"org.learning-observer.coding.programming_skills\",\n        'scope': coding_analyzer.assignment_scope,\n        'function': coding_analyzer.code_similarity,\n        'default': {'similarity_index': 0}\n    },\n]\n```\n</reducers>\n<ideal_output>\n<dag_planning>\nRelevant reducers:\n1. code_complexity: This reducer is directly relevant to calculating the code complexity for each student's submission.\n\nStep-by-step plan for DAG structure:\n1. Fetch the course roster\n2. Retrieve code complexity scores for each student\n3. Join the roster data with the complexity scores\n4. Format the results into a comprehensive report\n\nPotential server-side functions needed:\n- A function to format the complexity report for each student\n</dag_planning>\n\n```python\nEXECUTION_DAG = {\n    'execution_dag': {\n        'roster': q.call('learning_observer.courseroster')(runtime=q.parameter('runtime'), course_id=q.parameter(\"course_id\", required=True)),\n        \n        'complexity_scores': q.select(\n            q.keys('coding_analyzer.reducers.code_complexity', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'),\n            fields={'complexity_score': 'complexity_score'}\n        ),\n        \n        'joined_data': q.join(\n            LEFT=q.variable('roster'),\n            RIGHT=q.variable('complexity_scores'),\n            LEFT_ON='user_id',\n            RIGHT_ON='provenance.provenance.STUDENT.value.user_id'\n        ),\n        \n        'formatted_results': q.map(\n            q.call('coding_analyzer.format_complexity_report'),\n            q.variable('joined_data')\n        )\n    },\n    'exports': {\n        'student_complexity_report': {\n            'returns': 'formatted_results',\n            'parameters': ['course_id']\n        }\n    }\n}\n\n# Server-side functions needed:\n@learning_observer.communication_protocol.integration.publish_function('coding_analyzer.format_complexity_report')\nasync def format_complexity_report(student_data):\n    \"\"\"\n    Format the complexity report for each student\n    \"\"\"\n    return {\n        'student_id': student_data.get('user_id'),\n        'student_name': student_data.get('name', 'Unknown'),\n        'complexity_score': student_data.get('complexity_score', 0),\n        'status': 'Needs Review' if student_data.get('complexity_score', 0) > 8 else 'Acceptable'\n    }\n```\n</ideal_output>\n</example>\n<example>\n<goal>\nFetch the roster for a specific course.\n</goal>\n<module>\nroster_info\n</module>\n<reducers>\n```python\nREDUCERS = []\n```\n</reducers>\n<ideal_output>\n<dag_planning>\nRelevant reducers:\n- No reducers are directly relevant to this task, as we only need to fetch the roster.\n\nStep-by-step plan for DAG structure:\n1. Use the learning_observer.courseroster function to fetch the roster for the specified course.\n2. Export the fetched roster data.\n\nPotential server-side functions needed:\n- No additional server-side functions are required for this simple task.\n</dag_planning>\n\n```python\nEXECUTION_DAG = {\n    'execution_dag': {\n        'roster': q.call('learning_observer.courseroster')(runtime=q.parameter('runtime'), course_id=q.parameter(\"course_id\", required=True)),\n    },\n    'exports': {\n        'roster_export': {\n            'returns': 'roster',\n            'parameters': ['course_id'],\n        }\n    }\n}\n```\n</ideal_output>\n</example>\n<example>\n<goal>\nFetch documents for students at a specific timestamp\n</goal>\n<module>\ndocument_analysis\n</module>\n<reducers>\n```python\nREDUCERS = [\n    {\n        'context': \"org.learning-observer.writing\",\n        'scope': document_analysis.student_scope,\n        'function': document_analysis.document_access_timestamps,\n        'default': {'timestamps': {}, 'last_document': ''}\n    }\n]\n```\n</reducers>\n<ideal_output>\n<dag_planning>\nRelevant reducers:\n1. document_access_timestamps: This reducer is crucial for fetching the document access timestamps for each student.\n\nStep-by-step plan for DAG structure:\n1. Fetch the course roster\n2. Retrieve document access timestamps for each student\n3. Use a server-side function to determine the appropriate document for each student at the specified timestamp\n4. Export the results\n\nPotential server-side functions needed:\n- A function to fetch the appropriate document for each student at a given timestamp\n</dag_planning>\n\n```python\nEXECUTION_DAG = {\n    'execution_dag': {\n        'roster': q.call('learning_observer.courseroster')(runtime=q.parameter('runtime'), course_id=q.parameter(\"course_id\", required=True)),\n        'timestamped_docs': q.select(q.keys('writing_observer.reducers.document_access_timestamps', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'), fields={'timestamps': 'timestamps'}),\n        'single_docs_at_ts': q.call('writing_observer.fetch_doc_at_timestamp')(overall_timestamps=q.variable('timestamped_docs'), requested_timestamp=q.parameter('requested_timestamp')),\n    },\n    'exports': {\n        'docs_export': {\n            'returns': 'single_docs_at_ts',\n            'parameters': ['course_id', 'requested_timestamp'],\n        },\n        'some_other_export': {\n            'returns': 'some_other_node',\n            'parameters': ['course_id'],\n        }\n    }\n}\n\n# Server-side functions:\n@learning_observer.communication_protocol.integration.publish_function('writing_observer.fetch_doc_at_timestamp')\nasync def fetch_doc_at_timestamp(overall_timestamps, requested_timestamp=None):\n    '''\n    Iterate over a list of students and determine their latest document\n    in reference to the `requested_timestamp`.\n\n    `requested_timestamp` should be a string of ms since unix epoch\n    '''\n    async for student in overall_timestamps:\n        timestamps = student.get('timestamps', {})\n        student['doc_id'] = ''\n        if requested_timestamp is None:\n            # perhaps this should fetch the latest doc id instead\n            yield student\n            continue\n        sorted_ts = sorted(timestamps.keys())\n        bisect_index = bisect.bisect_right(sorted_ts, requested_timestamp) - 1\n        if bisect_index < 0:\n            yield student\n            continue\n        target_ts = sorted_ts[bisect_index]\n        student['doc_id'] = timestamps[target_ts]\n        yield student\n```\n</ideal_output>\n</example>\n</examples>\n\n"
                    },
                    {
                        "type": "text",
                        "text": "You are a query generator for a system that uses a DAG-based communication protocol. Your task is to generate valid Directed Acyclic Graphs (DAGs) based on user requests, along with any additional server-side functions required for the DAG to work.\n\n<context>\n<reducers>\n{{reducers}}\n</reducers>\n\n<module>\n{{module}}\n</module>\n\n<goal>\n{{goal}}\n</goal>\n</context>\n\nGiven this context, you need to create an EXECUTION_DAG that achieves the specified goal using the available reducers and module information. Follow these steps:\n\n<instructions>\n\n1. Analyze the input:\n   - Carefully read the goal and understand what needs to be accomplished.\n   - Review the list of reducers and identify which ones are relevant to the goal.\n   - Consider the module name and how it relates to the task.\n\n2. Design the DAG structure:\n   - Plan the sequence of operations needed to achieve the goal.\n   - Determine which reducers, if any, need to be queried.\n   - Identify any necessary data transformations or joins.\n\n3. Implement the EXECUTION_DAG:\n   - Use the following operations as needed:\n     - `call`: Invoke server-side functions using `q.call('module.function_name')`.\n     - `keys`: Format data into keys for selection.\n     - `select`: Fetch data from the Key-Value Store (KVS).\n     - `join`: Merge two datasets based on matching keys.\n     - `map`: Apply transformations to data using server-side functions.\n     - `parameter`: Allow user-specified inputs.\n   - Ensure variable names are **descriptive** and follow a consistent naming pattern derived from reducers.  \n\n4. Define the exports:\n   - The output must be structured as:  \n     ```python\n     'exports': {\n         'export_name': {\n             'returns': 'dag_output_variable',\n             'parameters': ['required_param1', 'optional_param2']\n         }\n     }\n     ```  \n   - Ensure exports clearly map to a valid DAG output.\n\n5. Create any necessary server-side functions:\n   - If the DAG requires additional functions, define them **after the DAG**.  \n   - Each function must include:  \n     - A clear function signature with required parameters.  \n     - Async implementation if applicable.  \n     - Proper integration decorators (e.g., `@learning_observer.communication_protocol.integration.publish_function`).  \n     - Input validation to handle missing or malformed data.\n\n6. Format the output:\n   - Structure the output as a Python dictionary with 'execution_dag' and 'exports' sections.\n   - Ensure the output adheres to the protocol's schema and is valid Python code.\n\n</instructions>\n\nBefore generating the final output, plan your approach in <dag_planning> tags:\n   - List out relevant reducers and explain their relevance to the goal.\n   - Create a step-by-step plan for the DAG structure.\n   - Identify any potential server-side functions that might be needed.\nThis will help ensure a thorough and well-thought-out solution.\n\nYour response should contain ONLY the generated code, without any explanations or additional text. The output should be ready to use in the system."
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "<dag_planning>"
                    }
                ]
            }
        ]
    )

    # Call sub-agent with formatted parameters
    response = agent(variables={
        'module': module,
        'goal': goal,
        'reducers': reducers
    })
    
    return json.dumps({
        'output': response,
    })


tools = [
    {
        'name': 'generate_communication_protocol_query',
        'description': 'Generate communication protocol query',
        'input_schema': {
            'type': 'object',
            'properties': {
                'module': {'type': 'string', 'description': 'The name of the module we are working in'},
                'goal': {'type': 'string', 'description': 'Our overall goal with the query'},
                'reducers': {'type': 'string', 'description': 'Python code representing the reducers available in our system.'}
            },
            'required': ['module', 'goal']
        },
        'function': generate_communication_protocol_query
    }
]


code = '''```python
REDUCERS = [
    {
        'context': "org.learning-observer.collaboration.group_projects",
        'scope': collaboration_analysis.group_scope,
        'function': collaboration_analysis.contribution_balance,
        'default': {'balance_score': 0.0}
    },
    {
        'context': "org.learning-observer.collaboration.group_projects",
        'scope': collaboration_analysis.student_scope,
        'function': collaboration_analysis.communication_frequency,
        'default': {'messages_per_day': 0}
    },
    {
        'context': "org.learning-observer.collaboration.group_projects",
        'scope': collaboration_analysis.project_scope,
        'function': collaboration_analysis.milestone_completion,
        'default': {'completed_milestones': 0, 'total_milestones': 0}
    },
    {
        'context': "org.learning-observer.collaboration.group_projects",
        'scope': collaboration_analysis.student_scope,
        'function': collaboration_analysis.task_assignment,
        'default': {'assigned_tasks': []}
    },
    {
        'context': "org.learning-observer.collaboration.group_projects",
        'scope': collaboration_analysis.group_scope,
        'function': collaboration_analysis.conflict_resolution,
        'default': {'resolved_conflicts': 0, 'open_conflicts': 0}
    },
    {
        'context': "org.learning-observer.collaboration.group_projects",
        'scope': collaboration_analysis.project_scope,
        'function': collaboration_analysis.resource_utilization,
        'default': {'resource_usage': {}}
    }
]
```
'''

response = generate_communication_protocol_query(
    module='collaboration_analysis',
    goal='Analyze group dynamics in collaborative projects by combining individual communication frequencies, task assignments, and contribution balance scores. Then, correlate this data with project milestone completion rates and conflict resolution metrics to identify high-performing teams and areas for improvement in group collaboration.',
    reducers=code
)

print(response)
