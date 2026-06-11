from typing import Any

class Vertex:
    """Represent a dialogue vertex (NPC node) in the graph.

    Attributes:
        vertex_name (str): Vertex identifier.
        text (str): Dialogue text shown at this vertex.
        effects (list[dict[str, str | int]]): Effects applied on entry.
    """

    def __init__(self, vertex_name: str, data: dict) -> None:
        """Initialize a vertex from normalized mapping data.

        Args:
            vertex_name (str): Vertex identifier.
            data (dict): Mapping containing "text" and "effects" keys.
        """
        self.vertex_name = vertex_name
        self.text = data["text"]
        self.effects = data["effects"] or []

    def __repr__(self) -> str:
        """Return a debug representation of this vertex.

        Returns:
            str: String representation of this vertex.
        """
        return (
            f'Vertex(vertex_name="{self.vertex_name}", '
            f'data={{"text": "{self.text}", "effects": {self.effects}}})'
        )

    def __eq__(self, other: Any) -> bool:
        """Compare this vertex with another object for value equality.

        Args:
            other (Any): Object to compare against.

        Returns:
            bool: "True" when all vertex fields match.
        """
        if not isinstance(other, Vertex):
            return NotImplemented
        return (
            self.vertex_name == other.vertex_name
            and self.text == other.text
            and self.effects  == other.effects
        )