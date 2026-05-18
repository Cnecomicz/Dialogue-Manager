from dialogue_model.codecs import convert_text_to_effect
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph
from dialogue_model.vertex import Vertex

class GraphEditor:
    def __init__(self, yaml_file: str = "") -> None:
        self.graph = Graph(yaml_file)

    def add_effect(self, vertex_or_edge_name: str, effect: str) -> None:
        effect = convert_text_to_effect(effect)
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.append(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.append(effect)

    def add_edge(
        self, 
        from_vertex: str, 
        to_vertex: str, 
        text: str, 
        predicates: list[dict[str, str | int]] = None, 
        effects: list[dict[str, str | int]] = None
    ) -> None:
        if predicates is None:
            predicates = []
        if effects is None:
            effects = []
        edge_name = f"{from_vertex}_to_{to_vertex}"
        self.graph.edge_dict[edge_name] = Edge(
            edge_name, {
                "from": from_vertex,
                "to": to_vertex,
                "text": text,
                "predicates": predicates,
                "effects": effects
            }
        )
        print(edge_name, self.graph.edge_dict[edge_name])

    def add_vertex(
        self, vertex_name: str, text: str, effects: list[dict[str, str | int]] = None
    ) -> None:
        if effects is None:
            effects = []
        self.graph.vertex_dict[vertex_name] = Vertex(
            vertex_name, {"text": text, "effects": effects}
        )

    def edit_vertex_text(self, vertex_name: str, text: str) -> None:
        self.graph.vertex_dict[vertex_name].text = text

    def remove_effect(self, vertex_or_edge_name: str, effect: str) -> None:
        effect = convert_text_to_effect(effect)
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.remove(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.remove(effect)
