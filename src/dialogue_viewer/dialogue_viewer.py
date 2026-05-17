from graphviz import Digraph

from dialogue_manager.graph import Graph

class DialogueViewer:
    def __init__(self, graph: Graph):
        self.graph = graph

    def convert_to_str(self, list_of_dicts: list):
        text = ""
        for item in list_of_dicts:
            text += "{"
            for key, value in item.items():
                text += f"{key}: {value}, "
            text = text[:-2] + r"}\l"
        return text



    def render(self):
        dot = Digraph(comment=self.graph.name)
        dot.attr(
            bgcolor="#181818",
            rankdir="TB",
            pad="0.5"
        )
        dot.attr(
            nodesep="0.5",
            ranksep="1.0"
        )
        dot.attr(
            "node",
            shape="box",
            style="rounded,filled",
            fillcolor="#333333",
            color="#aaaaaa",
            fontcolor="#e6e6e6",
            fontname="Helvetica",
            margin="0.2"
        )
        dot.attr(
            "edge",
            color="#cccccc",
            fontcolor="#e6e6e6",
            fontname="Helvetica"
        )
        for vertex_name, vertex in self.graph.vertex_dict.items():
            dialogue_text = fr"TEXT:\l{vertex.text}\l\l"
            effects_text = r"EFFECTS:\l" + self.convert_to_str(vertex.effects)
            dot.node(vertex_name, dialogue_text+effects_text)
        for edge_name, edge in self.graph.edge_dict.items():
            dialogue_text = fr"TEXT:\l{edge.text}\l\l"
            if edge.filters:
                filters_text = (
                    r"FILTERS:\l" + self.convert_to_str(edge.filters) + r"\l\l"
                )
            else:
                filters_text = ""
            if edge.effects:
                effects_text = (
                    r"EFFECTS:\l" + self.convert_to_str(edge.effects)
                )
            else:
                effects_text = ""
            dot.edge(
                edge.from_vertex.vertex_name, 
                edge.to_vertex.vertex_name, 
                label=dialogue_text+filters_text+effects_text
            )
        dot.render(f"data/{self.graph.name}_dialogue_graph", format="svg", cleanup=True)