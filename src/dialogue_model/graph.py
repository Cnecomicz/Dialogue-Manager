from yaml import safe_load

from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

class Graph:
    def __init__(self, yaml_file: str = "") -> None:
        yaml_data = self.get_yaml(yaml_file)
        normalized_data = self.normalize_yaml(yaml_data)
        self.name = normalized_data["name"]
        self.vertex_dict = {
            vertex_name: Vertex(vertex_name, data)
            for vertex_name, data in normalized_data["vertices"].items()
        }
        self.edge_dict = {
            edge_name: Edge(edge_name, data)
            for edge_name, data in normalized_data["edges"].items()
        }

    def get_yaml(self, yaml_file: str) -> dict:
        if yaml_file == "":
            return {}
        else:
            with open(yaml_file, 'r') as f:
                return safe_load(f) or {}

    def normalize_yaml(self, data: dict) -> dict:
        return {
            "name": data.get("name", ""),
            "vertices": data.get("vertices", {}),
            "edges": data.get("edges", {}),
        }