from os import PathLike
from typing import Any
from yaml import safe_dump

from dialogue_model.codecs import (
    convert_text_to_effect, convert_text_to_predicate
)
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph
from dialogue_model.vertex import Vertex

class GraphEditor:
    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        self.yaml_file = yaml_file
        self.graph = Graph(self.yaml_file)
        self.next_vertex_index = 0
        self.next_edge_index = 0

    def __repr__(self) -> str:
        return f'GraphEditor(yaml_file="{self.yaml_file}")'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GraphEditor):
            return NotImplemented
        return self.graph == other.graph

    def add_edge(
        self, 
        from_vertex: str, 
        to_vertex: str | None = None, 
        text: str | None = None, 
        predicates: list[dict[str, str | int]] = None, 
        effects: list[dict[str, str | int]] = None
    ) -> None:
        if to_vertex is None:
            self.add_vertex()
            to_vertex = f"vertex_{self.next_vertex_index-1}"
        if predicates is None:
            predicates = []
        if effects is None:
            effects = []
        edge_name = f"edge_{self.next_edge_index}"
        self.graph.edge_dict[edge_name] = Edge(
            edge_name, {
                "from": from_vertex,
                "to": to_vertex,
                "text": text,
                "predicates": predicates,
                "effects": effects
            }
        )
        self.next_edge_index += 1

    def add_effect(self, vertex_or_edge_name: str, effect: str) -> None:
        effect = convert_text_to_effect(effect)
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.append(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.append(effect)

    def add_predicate(self, edge_name: str, predicate: str) -> None:
        predicate = convert_text_to_predicate(predicate)
        self.graph.edge_dict[edge_name].predicates.append(predicate)

    def add_vertex(
        self, 
        text: str | None = None, 
        effects: list[dict[str, str | int]] = None
    ) -> None:
        if effects is None:
            effects = []
        vertex_name = f"vertex_{self.next_vertex_index}"
        self.graph.vertex_dict[vertex_name] = Vertex(
            vertex_name, {"text": text, "effects": effects}
        )
        self.next_vertex_index += 1

    def edit_edge_text(self, edge_name: str, text: str) -> None:
        self.graph.edge_dict[edge_name].text = text

    def edit_from_vertex(self, edge_name: str, from_vertex: str) -> None:
        self.graph.edge_dict[edge_name].from_vertex = from_vertex

    def edit_name(self, name: str) -> None:
        self.graph.name = name

    def edit_to_vertex(self, edge_name: str, to_vertex: str) -> None:
        self.graph.edge_dict[edge_name].to_vertex = to_vertex

    def edit_vertex_text(self, vertex_name: str, text: str) -> None:
        self.graph.vertex_dict[vertex_name].text = text

    def remove_edge(self, edge_name: str) -> None:
        del self.graph.edge_dict[edge_name]

    def remove_effect(self, vertex_or_edge_name: str, effect: str) -> None:
        effect = convert_text_to_effect(effect)
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.remove(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.remove(effect)

    def remove_predicate(self, edge_name: str, predicate: str) -> None:
        predicate = convert_text_to_predicate(predicate)
        self.graph.edge_dict[edge_name].predicates.remove(predicate)

    def remove_vertex(
        self, vertex_name: str, cascade_delete: bool = False
    ) -> None:
        if cascade_delete:
            edges_to_remove = [
                edge_name
                for edge_name, edge in self.graph.edge_dict.items()
                if edge.from_vertex == vertex_name
                or edge.to_vertex == vertex_name
            ]
            for edge_name in edges_to_remove:
                self.remove_edge(edge_name)
        for edge_name, edge in self.graph.edge_dict.items():
            if edge.from_vertex == vertex_name:
                self.edit_from_vertex(edge_name, "")
            if edge.to_vertex == vertex_name:
                self.edit_to_vertex(edge_name, "")
        del self.graph.vertex_dict[vertex_name]

    def save(self, yaml_file: str | PathLike | None = None) -> None:
        if yaml_file is None:
            yaml_file = self.yaml_file
        yaml_data = {
            "name": self.graph.name,
            "vertices": {
                vertex_name: {
                    "text": vertex.text, 
                    "effects": vertex.effects
                }
                for vertex_name, vertex in self.graph.vertex_dict.items()
            },
            "edges": {
                edge_name: {
                    "from": edge.from_vertex, 
                    "to": edge.to_vertex,
                    "text": edge.text,
                    "predicates": edge.predicates,
                    "effects": edge.effects
                }
                for edge_name, edge in self.graph.edge_dict.items()
            },
        }
        with open(yaml_file, "w") as f:
            safe_dump(yaml_data, f)
