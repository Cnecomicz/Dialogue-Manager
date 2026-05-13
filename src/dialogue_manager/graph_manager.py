from dialogue_manager.edge import Edge
from dialogue_manager.graph import Graph
from dialogue_manager.helper_functions import get_operator, get_nested_attr

class InvalidEdgeError(Exception):
    pass

class GraphManager:
    def __init__(self, graph: Graph, game_state: "GameState"):
        self.graph = graph
        self.game_state = game_state
        self.current_vertex = self.graph.vertex_dict["begin"]

    @property
    def current_edges(self):
        current_edges = {}
        for edge_name, edge in self.graph.edge_dict.items():
            if (edge.from_vertex == self.current_vertex 
            and self.evaluate_edge_filters(edge)):
                current_edges[edge_name] = edge
        return current_edges

    def evaluate_edge_filters(self, edge: Edge):
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


    