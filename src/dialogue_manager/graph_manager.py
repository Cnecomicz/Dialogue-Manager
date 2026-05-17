from dialogue_manager.edge import Edge
from dialogue_manager.graph import Graph
from dialogue_manager.vertex import Vertex
from dialogue_manager.helper_functions import (
    get_operator, get_nested_attr, set_nested_attr
)

class InvalidEdgeError(Exception):
    pass

class GraphManager:
    def __init__(self, graph: Graph, game_state: "GameState") -> None:
        self.graph = graph
        self.game_state = game_state
        self.current_vertex = self.graph.vertex_dict["begin"]

    @property
    def current_edges(self) -> dict[str, Edge]:
        current_edges = {}
        for edge_name, edge in self.graph.edge_dict.items():
            if (edge.from_vertex == self.current_vertex 
            and self.evaluate_edge_filters(edge)):
                current_edges[edge_name] = edge
        return current_edges

    def enter_vertex(self, vertex: Vertex) -> None:
        for effect in vertex.effects:
            self.proc_effect(effect)
        self.current_vertex = vertex

    def evaluate_edge_filters(self, edge: Edge) -> bool:
        is_valid_edge = True
        for condition in edge.filters:
            match condition["type"]:
                case "check_value":
                    operator_function = get_operator(condition["op"])
                    current_value = get_nested_attr(
                        self.game_state, condition["path"]
                    )
                    filter_value = condition["value"]
                    if not(operator_function(current_value, filter_value)):
                        is_valid_edge = False
        return is_valid_edge

    def get_current_edges(self) -> list[str]:
        return list(self.current_edges.keys())

    def proc_effect(self, effect: dict[str, str]) -> None:
        match effect["type"]:
            case "modify_value":
                target_value = get_nested_attr(
                    self.game_state, effect["target"]
                )
                new_value = target_value + effect["delta"]
                set_nested_attr(self.game_state, effect["target"], new_value)
            case "modify_list":
                match effect["method"]:
                    case "append":
                        target_list = get_nested_attr(
                            self.game_state, effect["target"]
                        )
                        target_list.append(effect["value"])
                    case "remove":
                        target_list = get_nested_attr(
                            self.game_state, effect["target"]
                        )
                        target_list.remove(effect["value"])

    def select(self, edge_name: str) -> None:
        if edge_name not in self.get_current_edges():
            raise InvalidEdgeError(
                f"Cannot select {edge_name} at vertex "
                f"{self.current_vertex} with the current game state. "
                f"{edge_name=}, "
                f"{self.current_vertex=}, "
                f"{self.graph=}, "
                f"{self.game_state=}"
            )
        edge = self.current_edges[edge_name]
        for effect in edge.effects:
            self.proc_effect(effect)
        vertex = self.graph.vertex_dict[edge.to_vertex.vertex_name]
        self.enter_vertex(vertex)


    