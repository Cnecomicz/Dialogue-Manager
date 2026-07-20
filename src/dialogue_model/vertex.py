from dataclasses import dataclass, field, KW_ONLY

@dataclass
class Vertex:
    """Represent a dialogue vertex (NPC node) in the graph.

    Attributes:
        vertex_name (str): Vertex identifier.
        text (str): Dialogue text shown at this vertex.
        effects (list[dict[str, str | int]]): Effects applied on entry.
    """

    vertex_name: str
    _: KW_ONLY
    text: str = ""
    effects: list[dict[str, str | int]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, vertex_name: str, data: dict) -> "Vertex":
        """Build a vertex from normalized mapping data.

        Args:
            vertex_name (str): Vertex identifier.
            data (dict): Mapping containing "text" and "effects" keys.

        Returns:
            Vertex: Vertex populated from the mapping.
        """
        return cls(
            vertex_name=vertex_name, 
            text=data["text"], 
            effects=data["effects"] or []
        )