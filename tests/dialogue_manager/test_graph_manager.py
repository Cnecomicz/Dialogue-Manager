from fixtures import hello_world_graph, mock_game_state

from dialogue_manager.graph_manager import GraphManager

# GraphManager has a current vertex that starts with "begin"
def test_starting_current_vertex(hello_world_graph):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    assert graph_manager.current_vertex == hello_world_graph.vertex_dict["begin"]

