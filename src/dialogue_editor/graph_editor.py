from dialogue_model.graph import Graph
from dialogue_model.vertex import Vertex

class GraphEditor:
    def __init__(self, yaml_file: str = "") -> None:
        self.graph = Graph(yaml_file)

    def add_vertex(
        self, vertex_name: str, text: str, effects: list[dict[str, str]] = None
    ) -> None:
        if effects is None:
            effects = []
        self.graph.vertex_dict[vertex_name] = Vertex(
            vertex_name, {"text": text, "effects": effects}
        )