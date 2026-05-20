from dialogue_manager.helper_functions import (
    get_operator, get_nested_attr, set_nested_attr
)
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph
from dialogue_model.vertex import Vertex

class InvalidEdgeError(Exception):
    pass

class GraphManager:
    def __init__(self, graph: Graph, game_state: "GameState") -> None:
        self.graph = graph
        self.game_state = game_state
        self.current_vertex = "vertex_0"

    @property
    def current_edges(self) -> dict[str, Edge]:
        current_edges = {}
        for edge_name, edge_obj in self.graph.edge_dict.items():
            if (edge_obj.from_vertex == self.current_vertex 
            and self.evaluate_edge_predicates(edge_name)):
                current_edges[edge_name] = edge_obj
        return current_edges

    def enter_vertex(self, vertex: str) -> None:
        vertex_obj = self.graph.vertex_dict[vertex]
        for effect in vertex_obj.effects:
            self.proc_effect(effect)
        self.current_vertex = vertex

    def evaluate_edge_predicates(self, edge: str) -> bool:
        edge_obj = self.graph.edge_dict[edge]
        is_valid_edge = True
        for predicate in edge_obj.predicates:
            match predicate["type"]:
                case "check_value":
                    operator_function = get_operator(predicate["op"])
                    current_value = get_nested_attr(
                        self.game_state, predicate["path"]
                    )
                    predicate_value = predicate["value"]
                    if not(operator_function(current_value, predicate_value)):
                        is_valid_edge = False
                case "check_list":
                    operator_function = get_operator(predicate["op"])
                    current_list = get_nested_attr(
                        self.game_state, predicate["path"]
                    )
                    predicate_value = predicate["value"]
                    if not(operator_function(predicate_value, current_list)):
                        is_valid_edge = False
        return is_valid_edge

    def get_current_edges(self) -> list[str]:
        return list(self.current_edges.keys())

    def proc_effect(self, effect: dict[str, str | int]) -> None:
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
        edge_obj = self.current_edges[edge_name]
        for effect in edge_obj.effects:
            self.proc_effect(effect)
        self.enter_vertex(edge_obj.to_vertex)


    