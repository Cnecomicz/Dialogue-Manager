from dialogue_model.codecs import (
    convert_effect_to_text, convert_predicate_to_text
)
from dialogue_model.graph import Graph

class CytoscapeAdapter:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    @property
    def edges(self) -> list[dict[str, dict[str, str]]]:
        edges = []
        for edge_name, edge in self.graph.edge_dict.items():
            edges.append(
                {"data": {"source": edge.from_vertex, "target": edge_name}}
            )
            edges.append(
                {"data": {"source": edge_name, "target": edge.to_vertex}}
            )
        return edges

    @property
    def nodes(self) -> list[dict[str, dict[str, str]]]:
        nodes = []
        # Nodes from vertices
        for vertex_name, vertex in self.graph.vertex_dict.items():
            effects_text = self.get_effects_text(vertex.effects)
            dialogue_text = f"TEXT:\n{vertex.text}"
            if effects_text:
                text = f"{effects_text}\n{dialogue_text}"
            else:
                text = dialogue_text
            nodes.append({"data": {"id": vertex_name, "label": text}})
        # Nodes from edges
        for edge_name, edge in self.graph.edge_dict.items():
            dialogue_text = f"TEXT:\n{edge.text}\n"
            predicates_text = self.get_predicates_text(edge.predicates)
            effects_text = self.get_effects_text(edge.effects)
            text = dialogue_text
            if predicates_text:
                text += f"\n{predicates_text}"
            if effects_text:
                text += f"\n{effects_text}"
                text = text[:-1]
            nodes.append({"data": {"id": edge_name, "label": text}})
        return nodes

    def get_effects_text(self, effects: list[dict[str, str | int]]) -> str:
        if effects:
            effects_text = "EFFECTS:\n"
            for effect in effects:
                effects_text += convert_effect_to_text(effect)+"\n"
        else:
            effects_text = ""
        return effects_text

    def get_predicates_text(self, predicates: list[dict[str, str | int]]) -> str:
        if predicates:
            predicates_text = "PREDICATES:\n"
            for predicate in predicates:
                predicates_text += convert_predicate_to_text(predicate)+"\n"
        else:
            predicates_text = ""
        return predicates_text