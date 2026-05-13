from dialogue_manager.edge import Edge
from dialogue_manager.graph import Graph

def get_nested_attr(obj: object, path: str):
    for attr in path.split("."):
        obj = getattr(obj, attr)
    return obj

class GraphManager:
    def __init__(self, graph: Graph, game_state: "GameState"):
        self.graph = graph
        self.game_state = game_state
        self.current_vertex = self.graph.vertex_dict["begin"]

    @property
    def current_edges(self):
        current_edges = {}
        for edge_name, edge in self.graph.edge_dict.items():
            if edge.from_vertex == self.current_vertex and self.evaluate_edge_filter(edge):
                current_edges[edge_name] = edge
        return current_edges

    def evaluate_edge_filter(self, edge: Edge):
        is_valid_edge = True
        for condition in edge.filters:
            match condition["type"]:
                case "check_value":
                    match condition["op"]:
                        case ">=": 
                            if not(get_nested_attr(self.game_state, condition["path"]) >= condition["value"]):
                                is_valid_edge = False
                        case "<":
                            if not(get_nested_attr(self.game_state, condition["path"]) < condition["value"]):
                                is_valid_edge = False
        return is_valid_edge


    