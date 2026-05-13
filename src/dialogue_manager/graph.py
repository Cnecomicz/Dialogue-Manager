from yaml import safe_load

from dialogue_manager.edge import Edge
from dialogue_manager.vertex import Vertex

class Graph:
    def __init__(self, yaml_file: str):
        with open(yaml_file, 'r') as f:
            yaml_data = safe_load(f)
        self.name = yaml_data["name"]
        self.vertices = {
            vertex_name: Vertex(vertex_name, data) 
            for vertex_name, data in yaml_data["vertices"].items()
        }
        self.edges = {
            edge_name: Edge(edge_name, data) 
            for edge_name, data in yaml_data["edges"].items()
        }
        for edge_name, edge in self.edges.items():
            edge.from_vertex = self.vertices[edge.from_vertex]
            edge.to_vertex = self.vertices[edge.to_vertex]