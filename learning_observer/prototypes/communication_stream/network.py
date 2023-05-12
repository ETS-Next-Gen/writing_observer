'''
Create mermaidjs charts in dash detailing the communication stream

`python network.py`
'''
import dash
from dash import html, dcc
from dash_extensions import Mermaid

flowchart = """
flowchart LR
subgraph roster
learning_observer.course_roster([Call: learning_observer.course_roster])
subgraph roster.kwargs
subgraph roster.kwargs.course
end
end
end
subgraph doc_ids
writing_observer.latest_doc[[Map: writing_observer.latest_doc]]
subgraph doc_ids.values
end
end
subgraph docs
subgraph docs.keys
end
end
subgraph combined
subgraph combined.left
end
subgraph combined.right
end
end
subgraph impl.roster.kwargs.course
course_id[/Parameter: course_id/]
end
subgraph impl.docs.keys
subgraph impl.docs.keys.doc_ids
end
end
impl.roster.kwargs.course --> roster.kwargs.course
roster --> doc_ids.values
impl.docs.keys --> docs.keys
docs --> combined.left
roster --> combined.right
doc_ids --> impl.docs.keys.doc_ids
"""

# module["module: string\nfilters: object\n#8195;students: list_of_students\n#8195;...\nparamters: object\n#8195;key: value"]
# style module text-align:left
app = dash.Dash()
app.layout = dcc.Tabs(
    [
        dcc.Tab(
            Mermaid(
                chart="""
                flowchart
                    subgraph client
                        ui[[Front End]]
                        subgraph request
                            direction TB
                            module{{"module: time_on_task"}}
                            filters{{"filters:\n#8195;students: courst_roster(current_course())"}}
                            parameters{{"parameters: paramters:\n#8195;threshold: 1"}}
                            style module text-align:left
                            style filters text-align:left
                            style parameters text-align:left
                        end
                        subgraph Websocket
                            wssend((Send))
                            wsrec((Receive))
                        end
                        ui -- creates --> request
                        request --> wssend
                    end
                    subgraph server
                        subgraph time_on_task
                            fetch[/"mod = fetch_module(module)"\]
                            collector[/"student_state = fetch_data(filters, mod.sources)"\]
                            fetch --> collector
                            M1("mod.sources.time_on_task") --> collector
                            transformer[/"transform_data(mod.transformers, student_state, parameters)"\]
                            collector --> transformer
                        end
                        subgraph ModuleHandler
                            modsend((Send))
                            modrec((Receive))
                        end
                        subgraph return
                            output{{"output: \n#8195;time_on_task: list_of_students"}}
                            style output text-align:left
                        end
                        modrec --> time_on_task
                        transformer --> output
                        return --> modsend
                    end
                    module -.-> fetch
                    filters -.-> collector
                    parameters -.-> transformer
                    wssend --> modrec
                    modsend --> wsrec
                    wsrec -- updates --> ui
                """
            ),
            label='Flow chart',
            value='flow'
        ),
        dcc.Tab(
            Mermaid(
                chart="""
                sequenceDiagram
                    Client->>Server: Connects to server
                    loop Every X seconds
                        activate Client
                        Note over Client: Prep request
                        Note right of Client: module: time_on_task
                        Note right of Client: filters: {students: courst_roster(current_course())}
                        Note right of Client: parameters: {threshold: 1}
                        Client->>Server: Send request
                        deactivate Client
                        activate Server
                        Note over Server: Process request
                        loop Over each module
                            Note right of Server: fetch_module(module)
                            Note right of Server: fetch_data(filters, mod.sources)
                            Note right of Server: transform_data(mod.transformers, student_state, parameters)
                        end
                        Note over Server: Collect output
                        Server->>Client: Response
                        deactivate Server
                        Note over Client: Update UI
                    end
                """
            ),
            label='Sequence diagram',
            value='seq'
        ),
        dcc.Tab(
            Mermaid(
                chart=flowchart
            ),
            label='DAG',
            value='dag'
        ),
    ],
    value='dag'
)

if __name__ == '__main__':
    app.run_server(debug=True)
