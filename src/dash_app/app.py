from os import PathLike

from dialogue_editor.graph_editor import GraphEditor
from dialogue_model.graph import Graph
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

class App:
    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        self.graph_editor = GraphEditor(yaml_file)
        self.graph = self.graph_editor.graph
        self.cytoscape_adapter = CytoscapeAdapter(self.graph)