from dash import Dash, html
from dash_cytoscape import Cytoscape, load_extra_layouts
from os import PathLike

from dialogue_editor.graph_editor import GraphEditor
from dialogue_model.graph import Graph
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

class App(Dash):
    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        super().__init__()
        self.graph_editor = GraphEditor(yaml_file)
        self.graph = self.graph_editor.graph
        self.cytoscape_adapter = CytoscapeAdapter(self.graph)
        load_extra_layouts()
        self.layout = html.Div([
            Cytoscape(
                id=f"{self.graph.name}",
                layout={"name": "dagre","rankDir": "TB"},
                style={
                    "width": "100%", 
                    "height": "100%", 
                    "background-color": "#303841"
                },
                elements=(
                    [node for node in self.cytoscape_adapter.nodes]
                    +[edge for edge in self.cytoscape_adapter.edges]
                ),
                stylesheet=[
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
            )
        ],
        style={"width": "100%", "height": "100vh"}
    )

if __name__ == "__main__":
    app = App("data/hello_world.yaml")
    app.run(debug=True)
