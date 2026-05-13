from fixtures import hello_world_graph, mock_game_state_with_gold

from dialogue_manager.graph_manager import GraphManager

# GraphManager has a current vertex that starts with "begin"
def test_starting_current_vertex(hello_world_graph):
    graph_manager = GraphManager(hello_world_graph, mock_game_state_with_gold)
    assert graph_manager.current_vertex == hello_world_graph.vertex_dict["begin"]

# GraphManager can return valid edge choices for your current vertex
def test_get_valid_edges(hello_world_graph):
    graph_manager = GraphManager(hello_world_graph, mock_game_state_with_gold)
    assert len(graph_manager.current_edges) == 2
    assert graph_manager.current_edges == {
        "begin_to_buy_flower": hello_world_graph.edge_dict["begin_to_buy_flower"],
        "begin_to_end": hello_world_graph.edge_dict["begin_to_end"]
    }
