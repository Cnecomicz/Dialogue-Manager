from typing import Any

from dialogue_model.vertex import Vertex

class Edge:
    """Represent a dialogue edge (effectively, player choice) in the graph.

    Attributes:
        edge_name (str): Edge identifier.
        from_vertex (str): Source vertex id.
        to_vertex (str): Target vertex id.
        text (str): Dialogue text for the choice.
        predicates (list[dict[str, str | int]]): Predicates gating selection.
        effects (list[dict[str, str | int]]): effects applied on selection.
    """

    def __init__(self, edge_name: str, data: dict) -> None:
        """Initialize an edge from normalized mapping data.

        Args:
            edge_name (str): Edge identifier.
            data (dict): Mapping containing edge fields.
        """
        self.edge_name = edge_name
        self.from_vertex = data["from"]
        self.to_vertex = data["to"]
        self.text = data["text"]
        self.predicates = data["predicates"] or []
        self.effects = data["effects"] or []

    def __repr__(self) -> str:
        """Return a debug representation of this edge.

        Returns:
            str: String representation of this edge.
        """
        return (
            f'Edge(edge_name="{self.edge_name}", '
            f'data={{"from": "{self.from_vertex}", '
            f'"to": "{self.to_vertex}", '
            f'"text": "{self.text}", '
            f'"predicates": {self.predicates}, '
            f'"effects": {self.effects}}})'
        )

    def __eq__(self, other: Any) -> bool:
        """Compare this edge with another object for value equality.

        Args: 
            other (Any): Object to compare against.

        Returns:
            bool: "True" when all edge fields match.
        """
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