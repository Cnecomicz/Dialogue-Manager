from graphviz import Digraph

from dialogue_manager.graph import Graph

class GraphViewer:
    def __init__(self, graph: Graph):
        self.graph = graph

    def convert_effect_to_str(self, effect: dict):
        match effect["type"]:
            case "modify_value":
                return (
                    effect["target"] + " = "
                    + effect["target"]
                    + str(effect["delta"])
                )
            case "modify_list":
                return (
                    effect["target"] + "."
                    + effect["method"] + "("
                    + effect["value"] + ")"
                )

    def convert_filter_to_str(self, condition: dict):
        match condition["type"]:
            case "check_value":
                return (
                    condition["path"] + " "
                    + condition["op"] + " "
                    + str(condition["value"])
                )

    def get_effects_text(self, effects: list):
        if effects:
            effects_text = r"\nEFFECTS:\n"
            for effect in effects:
                effects_text += self.convert_effect_to_str(effect)+r"\n"
        else:
            effects_text = ""
        return effects_text

    def get_filters_text(self, filters: list):
        if filters:
            filters_text = r"\nFILTERS:\n"
            for condition in filters:
                filters_text += self.convert_filter_to_str(condition)+r"\n"
        else:
            filters_text = ""
        return filters_text


    def render(self):
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
            dialogue_text = fr"TEXT:\n{vertex.text}\n"
            effects_text = self.get_effects_text(vertex.effects)
            dot.node(
                vertex_name, 
                dialogue_text+effects_text,
                shape="box",
                style="rounded,filled",
                fillcolor="#a36a2a",
                color="#aaaaaa"
            )
        for edge_name, edge in self.graph.edge_dict.items():
            dialogue_text = fr"TEXT:\n{edge.text}\n"
            filters_text = self.get_filters_text(edge.filters)
            effects_text = self.get_effects_text(edge.effects)
            dot.node(
                edge_name,
                dialogue_text+filters_text+effects_text,
                # shape="circle",
                style="filled",
                fillcolor="#336699",
                color="#aaaaaa"
            )
            dot.edge(
                edge.from_vertex.vertex_name, 
                edge_name
            )
            dot.edge(
                edge_name,
                edge.to_vertex.vertex_name
            )
        dot.render(f"data/{self.graph.name}_dialogue_graph", format="svg", cleanup=True)