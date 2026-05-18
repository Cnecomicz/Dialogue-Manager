from pytest import raises

from dialogue_manager.graph_manager import GraphManager, InvalidEdgeError

# GraphManager has a current vertex that starts with "begin"
def test_starting_current_vertex(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    assert graph_manager.current_vertex == "begin"

# GraphManager keeps track of valid edge choices for your current vertex
def test_has_valid_edges(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    assert len(graph_manager.current_edges) == 2
    assert graph_manager.current_edges == {
        "begin_to_buy_flower": hello_world_graph.edge_dict["begin_to_buy_flower"],
        "begin_to_end": hello_world_graph.edge_dict["begin_to_end"]
    }

# You can't select an edge if it's not valid
def test_error_when_selecting_invalid_edge(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    with raises(InvalidEdgeError):
        graph_manager.select("begin_to_insufficient_gold")

# Selecting a valid edge causes its effects to occur
def test_select_edge_to_cause_effects(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    graph_manager.select("begin_to_buy_flower")
    assert mock_game_state.player.gold == 1

# Selecting an edge updates your current vertex
def test_select_edge_to_go_to_next_vertex(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    graph_manager.select("begin_to_buy_flower")
    assert graph_manager.current_vertex == "buy_flower"

# If the game state changes mid conversation, the valid edges change to reflect that
def test_error_when_selecting_invalid_edge_that_was_previously_valid(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    graph_manager.select("begin_to_buy_flower")
    graph_manager.select("buy_flower_to_buy_flower")
    with raises(InvalidEdgeError):
        graph_manager.select("buy_flower_to_buy_flower")

# You can get a list of valid edges as strs
def test_get_valid_edges(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    assert graph_manager.get_current_edges() == ["begin_to_buy_flower", "begin_to_end"]

# Entering a vertex causes its effects to procure
def test_new_vertex_causes_effects(hello_world_graph, mock_game_state):
    graph_manager = GraphManager(hello_world_graph, mock_game_state)
    assert mock_game_state.player.inventory == []
    assert mock_game_state.alice.inventory == ["Flower", "Flower"]
    graph_manager.select("begin_to_buy_flower")
    assert mock_game_state.player.inventory == ["Flower"]
    assert mock_game_state.alice.inventory == ["Flower"]

# Edge filters can be ANDed
def test_edge_filter_1_and_filter_2(hello_world_graph, mock_game_state_with_limited_inventory):
    graph_manager = GraphManager(hello_world_graph, mock_game_state_with_limited_inventory)
    graph_manager.select("begin_to_buy_flower")
    with raises(InvalidEdgeError):
        graph_manager.select("buy_flower_to_buy_flower")
    graph_manager.select("buy_flower_to_insufficient_flowers")