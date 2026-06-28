from dialogue_model.codecs import (
    convert_effect_to_text, convert_predicate_to_text
)
from dialogue_model.graph import Graph

class CytoscapeAdapter:
    """Adapt a graph model to Dash Cytoscape nodes and edges."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the adapter with a dialogue graph.

        Args:
            graph (Graph): Source dialogue graph.
        """
        self.graph = graph

    @property
    def edges(self) -> list[dict[str, dict[str, str]]]:
        """Build Cytoscape edge elements from graph connectivity.

        Returns:
            list[dict[str, dict[str, str]]]: Cytoscape edge elements.
        """
        edges = []
        for edge_name, edge in self.graph.edge_dict.items():
            if (
                edge.from_vertex 
                and edge.from_vertex != "__MISSING__" 
                and edge.from_vertex in self.graph.vertex_dict
            ):
                edges.append(
                    {"data": {"source": edge.from_vertex, "target": edge_name}}
                )
            if (
                edge.to_vertex
                and edge.to_vertex != "__MISSING__"
                and edge.to_vertex in self.graph.vertex_dict
            ):
                edges.append(
                    {"data": {"source": edge_name, "target": edge.to_vertex}}
                )
        return edges

    @property
    def nodes(self) -> list[dict[str, dict[str, str]]]:
        """Build Cytoscape node elements for vertices and edges.

        Returns:
            list[dict[str, dict[str, str]]]: Cytoscape node elements.
        """
        nodes = []
        # Nodes from vertices
        for vertex_name, vertex in self.graph.vertex_dict.items():
            effects_text = self.get_effects_text(vertex.effects)
            dialogue_text = f"TEXT:\n{vertex.text}"
            if effects_text:
                text = f"{effects_text}\n{dialogue_text}"
            else:
                text = dialogue_text
            if vertex_name == "vertex_0":
                text = f"START\n\n{text}"
                nodes.append(
                    {
                        "data": {
                            "id": vertex_name,
                            "label": text,
                            "is_start_vertex": True
                        }
                    }
                )
            else:
                nodes.append({"data": {"id": vertex_name, "label": text}})
        # Nodes from edges
        for edge_name, edge in self.graph.edge_dict.items():
            has_missing_from = edge.from_vertex == "__MISSING__"
            has_missing_to = edge.to_vertex == "__MISSING__"
            unresolved_text = ""
            if has_missing_from:
                unresolved_text += "FROM: missing\n"
            if has_missing_to:
                unresolved_text += "TO: missing\n"
            dialogue_text = f"TEXT:\n{edge.text}\n"
            predicates_text = self.get_predicates_text(edge.predicates)
            effects_text = self.get_effects_text(edge.effects)
            text = unresolved_text + dialogue_text
            if predicates_text:
                text += f"\n{predicates_text}"
            if effects_text:
                text += f"\n{effects_text}"
                text = text[:-1]
            nodes.append(
                {
                    "data": {
                        "id": edge_name, 
                        "label": text, 
                        "is_edge_node": True,
                        "has_missing_endpoint": (
                            has_missing_from or has_missing_to
                        )
                    }
                }
            )
        return nodes

    def get_effects_text(self, effects: list[dict[str, str | int]]) -> str:
        """Render effects as a human-readable text block.

        Args:
            effects (list[dict[str, str | int]]): Effect mappings.

        Returns:
            str: Prefixed multiline effects text.
        """
        if effects:
            effects_text = "EFFECTS:\n"
            for effect in effects:
                effects_text += convert_effect_to_text(effect)+"\n"
        else:
            effects_text = ""
        return effects_text

    def get_predicates_text(
        self, predicates: list[dict[str, str | int]]
    ) -> str:
        """Render predicates as a human-readable text block.

        Args:
            predicates (list[dict[str, str | int]]): Predicate mappings.

        Returns:
            str: Prefixed multiline predicates text.
        """
        if predicates:
            predicates_text = "PREDICATES:\n"
            for predicate in predicates:
                predicates_text += convert_predicate_to_text(predicate)+"\n"
        else:
            predicates_text = ""
        return predicates_text