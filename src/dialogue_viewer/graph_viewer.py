from graphviz import Digraph

from dialogue_model.graph import Graph
from dialogue_model.codecs import (
    convert_effect_to_text, convert_filter_to_text
)

class GraphViewer:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def get_effects_text(self, effects: list[dict[str, str]]) -> str:
        if effects:
            effects_text = r"EFFECTS:\n"
            for effect in effects:
                effects_text += convert_effect_to_text(effect)+r"\n"
        else:
            effects_text = ""
        return effects_text

    def get_filters_text(self, filters: list[dict[str, str]]) -> str:
        if filters:
            filters_text = r"FILTERS:\n"
            for condition in filters:
                filters_text += convert_filter_to_text(condition)+r"\n"
        else:
            filters_text = ""
        return filters_text


    def render(self) -> None:
        dot = Digraph(comment=self.graph.name)
        dot.attr(
            bgcolor="#303841",
            rankdir="TB",
            pad="0.5"
        )
        dot.attr(
            nodesep="0.5",
            ranksep="1.0"
        )
        dot.attr(
            "node",
            fontcolor="#e6e6e6",
            fontname="Helvetica",
            justify="center",
            margin="0.25,0.1"
        )
        dot.attr(
            "edge",
            color="#cccccc",
            fontcolor="#e6e6e6",
            fontname="Helvetica",
        )
        for vertex_name, vertex in self.graph.vertex_dict.items():
            effects_text = self.get_effects_text(vertex.effects)
            dialogue_text = fr"TEXT:\n{vertex.text}"
            if effects_text:
                text = fr"{effects_text}\n{dialogue_text}"
            else:
                text = dialogue_text
            dot.node(
                vertex_name, 
                text,
                shape="box",
                style="rounded,filled",
                fillcolor="#a36a2a",
                color="#aaaaaa"
            )
        for edge_name, edge in self.graph.edge_dict.items():
            dialogue_text = fr"TEXT:\n{edge.text}\n"
            filters_text = self.get_filters_text(edge.filters)
            effects_text = self.get_effects_text(edge.effects)
            text = dialogue_text
            if filters_text:
                text += fr"\n{filters_text}"
            if effects_text:
                text += fr"\n{effects_text}"
            dot.node(
                edge_name,
                text,
                style="filled",
                fillcolor="#336699",
                color="#aaaaaa"
            )
            dot.edge(
                edge.from_vertex, 
                edge_name
            )
            dot.edge(
                edge_name,
                edge.to_vertex
            )
        dot.render(f"data/{self.graph.name}_dialogue_graph", format="svg", cleanup=True)