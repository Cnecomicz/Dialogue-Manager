from dialogue_manager.graph import Graph

class GraphManager:
    def __init__(self, graph: Graph, game_state: "GameState"):
        self.graph = graph
        self.game_state = game_state
        self.current_vertex = self.graph.vertex_dict["begin"]