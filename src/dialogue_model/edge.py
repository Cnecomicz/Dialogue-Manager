from dialogue_model.vertex import Vertex

class Edge:
    def __init__(self, edge_name: str, data: dict) -> None:
        self.edge_name = edge_name
        self.from_vertex = data["from"]
        self.to_vertex = data["to"]
        self.text = data["text"]
        self.predicates = data["predicates"]
        self.effects = data["effects"]

    def __repr__(self) -> str:
        return (
            f'Edge(edge_name="{self.edge_name}", '
            f'data={{"from": "{self.from_vertex}", '
            f'"to": "{self.to_vertex}", '
            f'"text": "{self.text}", '
            f'"predicates": {self.predicates}, '
            f'"effects": {self.effects}}})'
        )

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return self.__dict__ == other.__dict__