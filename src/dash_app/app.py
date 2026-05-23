from dash import Dash, dcc, html, Input, Output, State
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
                                "padding": "8px 10px",
                                "fontSize": "14px",
                                "opacity": 1
                            }
                        ),
                        html.Button("Save text", id="save-text", n_clicks=0)
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
                        "background-color": "#303841"
                    },
                    elements=self.get_elements(),
                    stylesheet=self.get_stylesheet()
                )
            ],
            style={"width": "100%", "height": "100vh"}
        )
        self.register_callbacks()

    def get_elements(self) -> list[dict[str, dict[str, str]]]:
        cytoscape_adapter = CytoscapeAdapter(self.graph_editor.graph)
        return cytoscape_adapter.nodes + cytoscape_adapter.edges

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
            Output("dialogue-graph", "elements"),
            Input("save-text", "n_clicks"),
            State("dialogue-graph", "tapNodeData"),
            State("edit-text", "value"),
            prevent_initial_call=True
        )
        def save_selected_node_text(
            n_clicks: int, tapped_node_data: dict | None, new_text: str | None
        ) -> list[dict[str, dict[str, str]]]:
            if not n_clicks:
                raise PreventUpdate
            if not tapped_node_data:
                raise PreventUpdate
            if new_text is None:
                raise PreventUpdate
            node_id = tapped_node_data.get("id")
            if not node_id:
                raise PreventUpdate
            if node_id in self.graph_editor.graph.vertex_dict:
                self.graph_editor.edit_vertex_text(node_id, new_text)
            elif node_id in self.graph_editor.graph.edge_dict:
                self.graph_editor.edit_edge_text(node_id, new_text)
            else:
                raise PreventUpdate
            return self.get_elements()

def main():
    open_url("http://localhost:8050")
    app = App("data/hello_world.yaml")
    app.run(debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
