from pytest import raises

from dialogue_navigator.graph_navigator import GraphNavigator, InvalidEdgeError

# GraphNavigator has a current vertex that starts with "begin"
def test_starting_current_vertex(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.current_vertex == "vertex_0"

# GraphNavigator keeps track of valid edge choices for your current vertex
def test_has_valid_edges(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert len(graph_navigator.current_edges) == 2
    assert graph_navigator.current_edges == {
        "edge_0": alice_graph.edge_dict["edge_0"],
        "edge_3": alice_graph.edge_dict["edge_3"]
    }

# You can't select an edge if it's not valid
def test_error_when_selecting_invalid_edge(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    with raises(InvalidEdgeError):
        graph_navigator.select("edge_2")

# Selecting a valid edge causes its effects to occur
def test_select_edge_to_cause_effects(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    graph_navigator.select("edge_0")
    assert mock_game_state.player.gold == 1

# Selecting an edge updates your current vertex
def test_select_edge_to_go_to_next_vertex(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    graph_navigator.select("edge_0")
    assert graph_navigator.current_vertex == "vertex_1"

# If the game state changes mid conversation, the valid edges change to reflect that
def test_error_when_selecting_invalid_edge_that_was_previously_valid(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    graph_navigator.select("edge_0")
    graph_navigator.select("edge_4")
    with raises(InvalidEdgeError):
        graph_navigator.select("edge_4")

# You can get a list of valid edges as strs
def test_get_valid_edges(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.get_current_edges() == ["edge_0", "edge_3"]

# Entering a vertex causes its effects to procure
def test_new_vertex_causes_effects(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert mock_game_state.player.inventory == []
    assert mock_game_state.alice.inventory == ["Flower", "Flower"]
    graph_navigator.select("edge_0")
    assert mock_game_state.player.inventory == ["Flower"]
    assert mock_game_state.alice.inventory == ["Flower"]

# Edge predicates can be ANDed
def test_edge_predicate_1_and_predicate_2(alice_graph, mock_game_state_with_limited_inventory):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state_with_limited_inventory)
    graph_navigator.select("edge_0")
    with raises(InvalidEdgeError):
        graph_navigator.select("buy_flower_to_buy_flower")
    graph_navigator.select("edge_5")

# You can get the current NPC dialogue text directly
def test_get_current_vertex_text(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.get_current_vertex_text() == "Hello. You have {player.gold} gold. Want to buy a flower?"

# You can get current edge texts as {edge_id: edge.text}
def test_get_current_edge_texts(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.get_current_edge_texts() == {"edge_0": "Yes, I'll buy a flower.", "edge_3": "No thanks."}

# You can get all current turn text in one payload
def test_get_current_turn(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.get_current_turn() == {"vertex_text": "Hello. You have {player.gold} gold. Want to buy a flower?", "edge_texts": {"edge_0": "Yes, I'll buy a flower.", "edge_3": "No thanks."}}

