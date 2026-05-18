from yaml import safe_load

from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

class Graph:
    def __init__(self, yaml_file: str) -> None:
        if yaml_file == "":
            yaml_data = {"name": "", "vertices": {}, "edges": {}}
        else:
            with open(yaml_file, 'r') as f:
                yaml_data = safe_load(f)
        self.name = yaml_data["name"]
        self.vertex_dict = self.initial_populate_vertices(yaml_data)
        self.edge_dict = self.initial_populate_edges(yaml_data)

    def initial_populate_edges(self, yaml_data: dict) -> dict[str, Edge]:
        return {
            edge_name: Edge(edge_name, data) 
            for edge_name, data in yaml_data["edges"].items()
        }

    def initial_populate_vertices(self, yaml_data: dict) -> dict[str, Vertex]:
        return {
            vertex_name: Vertex(vertex_name, data) 
            for vertex_name, data in yaml_data["vertices"].items()
        }