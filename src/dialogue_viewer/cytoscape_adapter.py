from dialogue_model.codecs import (
    convert_effect_to_text, convert_predicate_to_text
)
from dialogue_model.graph import Graph

class CytoscapeAdapter:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    @property
    def nodes(self) -> list[dict[str, dict[str, str]]]:
        nodes = []
        for vertex_name, vertex in self.graph.vertex_dict.items():
            effects_text = self.get_effects_text(vertex.effects)
            dialogue_text = f"TEXT:\n{vertex.text}"
            if effects_text:
                text = f"{effects_text}\n{dialogue_text}"
            else:
                text = dialogue_text
            nodes.append({"data": {"id": vertex_name, "label": text}})
        print(nodes)
        return nodes

    def get_effects_text(self, effects: list[dict[str, str | int]]) -> str:
        if effects:
            effects_text = "EFFECTS:\n"
            for effect in effects:
                effects_text += convert_effect_to_text(effect)+"\n"
        else:
            effects_text = ""
        return effects_text