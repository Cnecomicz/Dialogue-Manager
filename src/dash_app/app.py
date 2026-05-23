from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import Cytoscape, load_extra_layouts
from os import PathLike
from webbrowser import open as open_url

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
                    [
                        html.H3("Edit selected node text"),
                        html.P("1) Click a node in the graph"),
                        html.P("2) Type new text"),
                        html.P("3) Click Save"),
                        html.Div(
                            "Selected node: None",
                            id="selected-node-display"
                        ),
                        dcc.Input(
                            id="edit-text",
                            type="text",
                            placeholder="Enter new text for selected node",
                            style={
                                "width": "100%",
                                "backgroundColor": "#ffffff",
                                "color": "#111827",
                                "caretColor": "#111827",
                                "border": "1px solid #9ca3af",
                                # "padding": "8px 10px",
                                "fontSize": "14px",
                                "opacity": 1
                            }
                        ),
                        html.Button("Save text", id="save-text", n_clicks=0),
                        html.Hr(),
                        html.H3("Add vertex"),
                        dcc.Input(
                            id="new-vertex-text",
                            type="text",
                            placeholder="Text for the new vertex",
                            style={
                                "width": "100%",
                                "backgroundColor": "#ffffff",
                                "color": "#111827",
                                "caretColor": "#111827",
                                "border": "1px solid #9ca3af",
                                # "padding": "8px 10px",
                                "fontSize": "14px",
                                "opacity": 1
                            }
                        ),
                        html.Button("Add vertex", id="add-vertex", n_clicks=0),
                        html.Hr(),
                        html.H3("Log"),
                        html.Div("Ready.",id="action-status")
                    ],
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
                    stylesheet=self.get_stylesheet()
                )
            ],
            style={"width": "100%", "height": "100vh"}
        )
        self.register_callbacks()

    def add_vertex(self, text: str | None) -> str:
        self.graph_editor.add_vertex(text)
        return f"vertex_{self.graph_editor.next_vertex_index-1}"

    def get_elements(self) -> list[dict[str, dict[str, str]]]:
        cytoscape_adapter = CytoscapeAdapter(self.graph_editor.graph)
        return cytoscape_adapter.nodes + cytoscape_adapter.edges

    def get_node_text(self, node_id: str) -> str | None:
        if node_id in self.graph_editor.graph.vertex_dict:
            return self.graph_editor.graph.vertex_dict[node_id].text
        if node_id in self.graph_editor.graph.edge_dict:
            return self.graph_editor.graph.edge_dict[node_id].text
        return None

    def get_stylesheet(self) -> list[dict[str, str | dict[str, str | int]]]:
        return [
            {
                "selector": "node",
                "style": {
                    "shape": "round-rectangle",
                    "background-color": "#a36a2a",
                    "border-color": "#aaaaaa",
                    "border-width": 2,
                    "color": "#e6e6e6",
                    "font-family": "Helvetica",
                    "font-size": "12px",
                    "label": "data(label)",
                    "text-valign": "center",
                    "text-halign": "center",
                    "text-wrap": "wrap",
                    "text-max-width": 240,
                    "min-width": 80,
                    "min-height": 40,
                    "width": "label",
                    "height": "label",
                    "padding": "20px"
                }
            },
            {
                "selector": "edge",
                "style": {
                    "line-color": "#cccccc",
                    "target-arrow-color": "#cccccc",
                    "target-arrow-shape": "triangle",
                    "color": "#e6e6e6",
                    "curve-style": "bezier"
                }
            },
            {
                "selector": "node:selected",
                "style": {
                    "border-color": "#fbbf24",
                    "border-width": 4
                }
            },
            {
                "selector": "[?is_edge_node]",
                "style": {
                    "shape": "ellipse",
                    "background-color": "#336699",
                    "padding": "30px"
                }
            }
        ]

    def register_callbacks(self) -> None:
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
            Output("action-status", "children"),
            Output("new-vertex-text", "value"),
            Input("save-text", "n_clicks"),
            Input("add-vertex", "n_clicks"),
            State("dialogue-graph", "selectedNodeData"),
            State("edit-text", "value"),
            State("new-vertex-text", "value"),
            prevent_initial_call=True
        )
        def handle_graph_updates(
            save_clicks: int,
            add_vertex_clicks: int,
            selected_nodes: list[dict] | None,
            new_text: str | None,
            new_vertex_text: str | None
        ) -> tuple[list[dict], str]:
            triggered_id = ctx.triggered_id
            if triggered_id == "add-vertex":
                if not new_vertex_text:
                    raise PreventUpdate
                new_vertex_name = self.add_vertex(new_vertex_text)
                return (self.get_elements(), f"Added {new_vertex_name}.", "")
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
                    f"Saved text for {node_id}.", 
                    no_update
                )
            raise PreventUpdate

    def update_node_text(self, node_id: str, new_text: str) -> bool:
        if node_id in self.graph_editor.graph.vertex_dict:
            self.graph_editor.edit_vertex_text(node_id, new_text)
            return True
        if node_id in self.graph_editor.graph.edge_dict:
            self.graph_editor.edit_edge_text(node_id, new_text)
            return True
        return False

def main():
    open_url("http://localhost:8050")
    app = App("data/hello_world.yaml")
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    main()
