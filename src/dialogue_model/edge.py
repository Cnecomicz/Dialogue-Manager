from dataclasses import dataclass, field, KW_ONLY

@dataclass
class Edge:
    """Represent a dialogue edge (effectively, player choice) in the graph.

    Attributes:
        edge_name (str): Edge identifier.
        from_vertex (str): Source vertex id.
        to_vertex (str): Target vertex id.
        text (str): Dialogue text for the choice.
        predicates (list[dict[str, str | int]]): Predicates gating selection.
        effects (list[dict[str, str | int]]): Effects applied on selection.
    """

    edge_name: str
    _: KW_ONLY
    from_vertex: str = ""
    to_vertex: str = ""
    text: str = ""
    predicates: list[dict[str, str | int]] = field(default_factory=list)
    effects: list[dict[str, str | int]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, edge_name: str, data: dict) -> "Edge":
        """Build an edge from normalized mapping data.

        Args:
            edge_name (str): Edge identifier.
            data (dict): Mapping containing edge fields.

        Returns:
            Edge: Edge populated from the mapping.
        """
        return cls(
            edge_name=edge_name,
            from_vertex=data["from"],
            to_vertex=data["to"],
            text=data["text"],
            predicates=data["predicates"] or [],
            effects=data["effects"] or []
        )