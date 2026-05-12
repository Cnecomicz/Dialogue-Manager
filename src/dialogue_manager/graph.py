from yaml import safe_load

from dialogue_manager.edge import Edge
from dialogue_manager.vertex import Vertex

class Graph:
    def __init__(self, yaml_file: str):
        with open(yaml_file, 'r') as f:
            yaml_data = safe_load(f)
        self.name = yaml_data["name"]
        self.vertices = [
            Vertex(name, data) for name, data in yaml_data["vertices"].items()
        ]
        self.edges = [
            Edge(name, data) for name, data in yaml_data["edges"].items()
        ]