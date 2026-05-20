from typing import Any

class Vertex:
    def __init__(self, vertex_name: str, data: dict) -> None:
        self.vertex_name = vertex_name
        self.text = data["text"]
        self.effects = data["effects"] or []

    def __repr__(self) -> str:
        return (
            f'Vertex(vertex_name="{self.vertex_name}", '
            f'data={{"text": "{self.text}", "effects": {self.effects}}})'
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Vertex):
            return NotImplemented
        return (
            self.vertex_name == other.vertex_name
            and self.text == other.text
            and self.effects  == other.effects
        )