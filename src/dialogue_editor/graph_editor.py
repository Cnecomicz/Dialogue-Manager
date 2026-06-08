from os import PathLike
from typing import Any
from yaml import safe_dump

from dialogue_model.edge import Edge
from dialogue_model.graph import Graph
from dialogue_model.vertex import Vertex

class GraphEditor:
    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        self.yaml_file = None
        self.graph = Graph()
        self.next_vertex_index = 0
        self.next_edge_index = 0
        if yaml_file is not None:
            self.load(yaml_file=yaml_file)

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
        if text is None:
            text = ""
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

    def add_effect(
        self, vertex_or_edge_name: str, effect: dict[str, str | int]
    ) -> None:
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.append(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.append(effect)

    def add_predicate(
        self, edge_name: str, predicate: dict[str, str | int]
    ) -> None:
        self.graph.edge_dict[edge_name].predicates.append(predicate)

    def add_vertex(
        self, 
        text: str | None = None, 
        effects: list[dict[str, str | int]] = None
    ) -> None:
        if text is None:
            text = ""
        if effects is None:
            effects = []
        vertex_name = f"vertex_{self.next_vertex_index}"
        self.graph.vertex_dict[vertex_name] = Vertex(
            vertex_name, {"text": text, "effects": effects}
        )
        self.next_vertex_index += 1

    def edit_edge_effects(
        self, edge_name: str, effects: list[dict[str, str | int]]
    ) -> None:
        self.graph.edge_dict[edge_name].effects = effects

    def edit_edge_predicates(
        self, edge_name: str, predicates: list[dict[str, str | int]]
    ) -> None:
        self.graph.edge_dict[edge_name].predicates = predicates

    def edit_edge_text(self, edge_name: str, text: str) -> None:
        self.graph.edge_dict[edge_name].text = text

    def edit_from_vertex(self, edge_name: str, from_vertex: str) -> None:
        self.graph.edge_dict[edge_name].from_vertex = from_vertex

    def edit_name(self, name: str) -> None:
        self.graph.name = name

    def edit_to_vertex(self, edge_name: str, to_vertex: str) -> None:
        self.graph.edge_dict[edge_name].to_vertex = to_vertex

    def edit_vertex_effects(
        self, vertex_name: str, effects: list[dict[str, str | int]]
    ) -> None:
        self.graph.vertex_dict[vertex_name].effects = effects

    def edit_vertex_text(self, vertex_name: str, text: str) -> None:
        self.graph.vertex_dict[vertex_name].text = text

    def export_yaml_text(self) -> str:
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
            }
        }
        return safe_dump(yaml_data, sort_keys=False)

    def get_next_edge_index(self) -> int:
        if not self.graph.edge_dict:
            return 0
        indices = []
        for edge_name in self.graph.edge_dict.keys():
            if edge_name.startswith("edge_"):
                indices.append(int(edge_name.split("_")[1]))
        return (
            max(max(indices)+1, len(self.graph.edge_dict))
            if indices else len(self.graph.edge_dict)
        )

    def get_next_vertex_index(self) -> int:
        if not self.graph.vertex_dict:
            return 0
        indices = []
        for vertex_name in self.graph.vertex_dict.keys():
            if vertex_name.startswith("vertex_"):
                indices.append(int(vertex_name.split("_")[1]))
        return (
            max(max(indices)+1, len(self.graph.vertex_dict)) 
            if indices else len(self.graph.vertex_dict)
        )

    def load(
        self, 
        yaml_file: str | PathLike | None = None, 
        yaml_data: dict | None = None
    ) -> None:
        self.yaml_file = yaml_file
        self.graph = Graph(yaml_file=yaml_file, yaml_data=yaml_data)
        self.next_vertex_index = self.get_next_vertex_index()
        self.next_edge_index = self.get_next_edge_index()

    def remove_edge(self, edge_name: str) -> None:
        del self.graph.edge_dict[edge_name]

    def remove_effect(
        self, vertex_or_edge_name: str, effect: dict[str, str | int]
    ) -> None:
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.remove(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.remove(effect)

    def remove_predicate(
        self, edge_name: str, predicate: dict[str, str | int]
    ) -> None:
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
                self.edit_from_vertex(edge_name, "__MISSING__")
            if edge.to_vertex == vertex_name:
                self.edit_to_vertex(edge_name, "__MISSING__")
        del self.graph.vertex_dict[vertex_name]

    def save(self, yaml_file: str | PathLike | None = None) -> None:
        if yaml_file is None:
            yaml_file = self.yaml_file
        if yaml_file is None:
            raise ValueError("No yaml file path is set for save().")
        yaml_data = self.export_yaml_text()
        with open(yaml_file, "w") as f:
            f.write(yaml_data)
