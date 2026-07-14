from graphviz import Digraph
from os import PathLike

from dialogue_model.constants import START_VERTEX
from dialogue_model.graph import Graph
from dialogue_model.codecs import (
    convert_effect_to_text, convert_predicate_to_text
)
from dialogue_viewer.theme import (
    COLOR_BACKGROUND,
    COLOR_EDGE_LINE,
    COLOR_EDGE_NODE_FILL,
    COLOR_FONT,
    COLOR_NODE_BORDER,
    COLOR_START_VERTEX_BORDER,
    COLOR_START_VERTEX_FILL,
    COLOR_VERTEX_FILL,
    LABEL_EFFECTS,
    LABEL_PREDICATES,
    LABEL_START,
    LABEL_TEXT
)

class GraphViewer:
    """Render dialogue graph yaml files into Graphviz SVG output."""

    def __init__(self, yaml_file: str | PathLike) -> None:
        """Initialize a viewer for a specific yaml graph file.

        Args:
            yaml_file (str | PathLike): Path to a .yaml or .yml file.
        """
        self.yaml_file = yaml_file

    def get_effects_text(self, effects: list[dict[str, str | int]]) -> str:
        """Format effect mappings as Graphviz label text.

        Args:
            effects (list[dict[str, str | int]]): Effect mappings.

        Returns:
            str: Escaped multiline effects block, or an empty string.
        """
        if effects:
            effects_text = fr"{LABEL_EFFECTS}\n"
            for effect in effects:
                effects_text += convert_effect_to_text(effect)+r"\n"
        else:
            effects_text = ""
        return effects_text

    def get_predicates_text(
        self, predicates: list[dict[str, str | int]]
    ) -> str:
        """Format predicate mappings as Graphviz label text.

        Args:
            predicates (list[dict[str, str | int]]): Predicate mappings.

        Returns:
            str: Escaped multiline predicates block, or an empty string.
        """
        if predicates:
            predicates_text = fr"{LABEL_PREDICATES}\n"
            for predicate in predicates:
                predicates_text += convert_predicate_to_text(predicate)+r"\n"
        else:
            predicates_text = ""
        return predicates_text


    def render(self) -> bool:
        """Render the yaml graph to an SVG file beside the source file.

        Returns:
            bool: "True" when rendering succeeds.
        """
        graph = Graph(yaml_file=self.yaml_file)
        dot = Digraph(comment=graph.name)
        dot.attr(
            bgcolor=COLOR_BACKGROUND,
            rankdir="TB",
            pad="0.5"
        )
        dot.attr(
            nodesep="0.5",
            ranksep="1.0"
        )
        dot.attr(
            "node",
            fontcolor=COLOR_FONT,
            fontname="Helvetica",
            justify="center",
            margin="0.25,0.1"
        )
        dot.attr(
            "edge",
            color=COLOR_EDGE_LINE,
            fontcolor=COLOR_FONT,
            fontname="Helvetica",
        )
        for vertex_name, vertex in graph.vertex_dict.items():
            effects_text = self.get_effects_text(vertex.effects)
            dialogue_text = fr"{LABEL_TEXT}\n{vertex.text}"
            if effects_text:
                text = fr"{effects_text}\n{dialogue_text}"
            else:
                text = dialogue_text
            fill_color = COLOR_VERTEX_FILL
            border_color = COLOR_NODE_BORDER
            if vertex_name == START_VERTEX:
                text = fr"{LABEL_START}\n\n{text}"
                fill_color = COLOR_START_VERTEX_FILL
                border_color = COLOR_START_VERTEX_BORDER
            dot.node(
                vertex_name, 
                text,
                shape="box",
                style="rounded,filled",
                fillcolor=fill_color,
                color=border_color
            )
        for edge_name, edge in graph.edge_dict.items():
            dialogue_text = fr"{LABEL_TEXT}\n{edge.text}\n"
            predicates_text = self.get_predicates_text(edge.predicates)
            effects_text = self.get_effects_text(edge.effects)
            text = dialogue_text
            if predicates_text:
                text += fr"\n{predicates_text}"
            if effects_text:
                text += fr"\n{effects_text}"
            dot.node(
                edge_name,
                text,
                style="filled",
                fillcolor=COLOR_EDGE_NODE_FILL,
                color=COLOR_NODE_BORDER
            )
            dot.edge(
                edge.from_vertex, 
                edge_name
            )
            dot.edge(
                edge_name,
                edge.to_vertex
            )
        if self.yaml_file.endswith(".yaml"):
            render_file = self.yaml_file[:-5]
        elif self.yaml_file.endswith(".yml"):
            render_file = self.yaml_file[:-4]
        else:
            return False
        dot.render(render_file, format="svg", cleanup=True)
        return True

def main() -> None:
    """Run a CLI prompt and render one yaml dialogue graph."""
    yaml_file = input("Enter file path (copy with Option-Command-C): ")
    graph_viewer = GraphViewer(yaml_file)
    result = graph_viewer.render()
    if not result:
        print("Render failed.")
    if result:
        print("Render successful.")