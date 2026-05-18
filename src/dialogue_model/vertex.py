from typing import Any

class Vertex:
    def __init__(self, vertex_name: str, data: dict) -> None:
        self.vertex_name = vertex_name
        self.text = data["text"]
        self.effects = data["effects"]

    def __repr__(self) -> str:
        return (
            f'Vertex(vertex_name="{self.vertex_name}", '
            f'data={{"text": "{self.text}", "effects": {self.effects}}})'
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Vertex):
            return NotImplemented
        return self.__dict__ == other.__dict__