from dialogue_manager.vertex import Vertex

class Edge:
    def __init__(self, edge_name: str, data: dict) -> None:
        self.edge_name = edge_name
        self.from_vertex = data["from"]
        self.to_vertex = data["to"]
        self.text = data["text"]
        self.filters = data["filters"]
        self.effects = data["effects"]

    def resolve_vertex_references(
        self, 
        vertex_dict: dict[str, Vertex]
    ) -> None:
        self.from_vertex = vertex_dict[self.from_vertex]
        self.to_vertex = vertex_dict[self.to_vertex]