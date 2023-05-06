import dash
from dash import html, dcc
from dash_extensions import Mermaid

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
        )
    ],
    value='seq'
)

if __name__ == '__main__':
    app.run_server(debug=True)
