from typing import Any

from dialogue_model.vertex import Vertex

class Edge:
    def __init__(self, edge_name: str, data: dict) -> None:
        self.edge_name = edge_name
        self.from_vertex = data["from"]
        self.to_vertex = data["to"]
        self.text = data["text"]
        self.predicates = data["predicates"] or []
        self.effects = data["effects"] or []

    def __repr__(self) -> str:
        return (
            f'Edge(edge_name="{self.edge_name}", '
            f'data={{"from": "{self.from_vertex}", '
            f'"to": "{self.to_vertex}", '
            f'"text": "{self.text}", '
            f'"predicates": {self.predicates}, '
            f'"effects": {self.effects}}})'
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return (
            self.edge_name == other.edge_name
            and self.from_vertex == other.from_vertex
            and self.to_vertex == other.to_vertex
            and self.text == other.text
            and self.predicates == other.predicates
            and self.effects == other.effects
        )