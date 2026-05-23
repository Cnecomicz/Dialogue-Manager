from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import Cytoscape, load_extra_layouts
from os import PathLike
from webbrowser import open as open_url

from dash_app.helper_functions import (
    get_add_vertex_button, get_cytoscape_stylesheet, get_edit_button, get_log
)
from dialogue_editor.graph_editor import GraphEditor
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

class App(Dash):
    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        super().__init__()
        self.graph_editor = GraphEditor(yaml_file)
        load_extra_layouts()
        self.layout = html.Div(
            [
                html.Div(
                    get_edit_button() 
                    + [html.Hr()] 
                    + get_add_vertex_button() 
                    + [html.Hr()]
                    + get_log(),
                    style={
                        "width": "320px",
                        "padding": "12px",
                        "backgroundColor": "#1f252b",
                        "color": "#e6e6e6",
                        "borderRight": "1px solid #444"
                    }
                ),
                Cytoscape(
                    id=f"dialogue-graph",
                    layout={"name": "dagre", "rankDir": "TB"},
                    style={
                        "width": "100%", 
                        "height": "100%", 
                        "backgroundColor": "#303841"
                    },
                    elements=self.get_elements(),
                    stylesheet=get_cytoscape_stylesheet()
                )
            ],
            style={"width": "100%", "height": "100vh"}
        )
        self.register_callbacks()

    def add_vertex(self, text: str | None) -> str:
        self.graph_editor.add_vertex(text)
        return f"vertex_{self.graph_editor.next_vertex_index-1}"

    def append_action_status(
        self, current_log: str | None, new_message: str
    ) -> str:
        if not current_log:
            return new_message
        return f"{current_log}\n{new_message}"

    def get_elements(self) -> list[dict[str, dict[str, str]]]:
        cytoscape_adapter = CytoscapeAdapter(self.graph_editor.graph)
        return cytoscape_adapter.nodes + cytoscape_adapter.edges

    def get_node_text(self, node_id: str) -> str | None:
        if node_id in self.graph_editor.graph.vertex_dict:
            return self.graph_editor.graph.vertex_dict[node_id].text
        if node_id in self.graph_editor.graph.edge_dict:
            return self.graph_editor.graph.edge_dict[node_id].text
        return None

    def register_callbacks(self) -> None:
        self.clientside_callback(
            """
            function(actionLog) {
                const logBox = document.getElementById("action-status");
                if (logBox) {
                    window.requestAnimationFrame(function() {
                        logBox.scrollTop = logBox.scrollHeight;
                    });
                }
                return "";
            }
            """,
            Output("action-status-scroll-trigger", "children"),
            Input("action-status", "value")
        )

        @self.callback(
            Output("edit-text", "value"),
            Input("dialogue-graph", "selectedNodeData")
        )
        def autofill_edit_text(selected_nodes: list[dict] | None) -> str:
            if not selected_nodes:
                return ""
            node_id = selected_nodes[0].get("id")
            if not node_id:
                return ""
            node_text = self.get_node_text(node_id)
            if node_text is None:
                return ""
            return node_text

        @self.callback(
            Output("selected-node-display", "children"),
            Input("dialogue-graph", "selectedNodeData")
        )
        def display_selected_node(selected_nodes: list[dict] | None) -> str:
            if not selected_nodes:
                return "Selected node: None"
            node_id = selected_nodes[0].get("id", "None")
            return f"Selected node: {node_id}"

        @self.callback(
            Output("dialogue-graph", "elements"),
            Output("action-status", "value"),
            Output("new-vertex-text", "value"),
            Input("save-text", "n_clicks"),
            Input("add-vertex", "n_clicks"),
            State("dialogue-graph", "selectedNodeData"),
            State("edit-text", "value"),
            State("new-vertex-text", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def handle_graph_updates(
            save_clicks: int,
            add_vertex_clicks: int,
            selected_nodes: list[dict] | None,
            new_text: str | None,
            new_vertex_text: str | None,
            current_log: str | None
        ) -> tuple[list[dict], str, str]:
            triggered_id = ctx.triggered_id
            if triggered_id == "add-vertex":
                if not new_vertex_text:
                    raise PreventUpdate
                new_vertex_name = self.add_vertex(new_vertex_text)
                return (
                    self.get_elements(), 
                    self.append_action_status(
                        current_log, f"Added {new_vertex_name}."
                    ),
                    ""
                )
            if triggered_id == "save-text":
                if not selected_nodes:
                    raise PreventUpdate
                if not new_text:
                    raise PreventUpdate
                node_id = selected_nodes[0].get("id")
                if not node_id:
                    raise PreventUpdate
                was_updated = self.update_node_text(node_id, new_text)
                if not was_updated:
                    raise PreventUpdate
                return (
                    self.get_elements(), 
                    self.append_action_status(
                        current_log, f"Saved text for {node_id}."
                    ),
                    no_update
                )
            raise PreventUpdate

    def update_node_text(self, node_id: str, new_text: str) -> bool:
        if node_id in self.graph_editor.graph.vertex_dict:
            if self.graph_editor.graph.vertex_dict[node_id].text == new_text:
                return False
            self.graph_editor.edit_vertex_text(node_id, new_text)
            return True
        if node_id in self.graph_editor.graph.edge_dict:
            if self.graph_editor.graph.edge_dict[node_id].text == new_text:
                return False
            self.graph_editor.edit_edge_text(node_id, new_text)
            return True
        return False

def main():
    open_url("http://localhost:8050")
    app = App("data/hello_world.yaml")
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    main()
