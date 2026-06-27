from pytest import raises

from dialogue_model.graph import Graph
from dialogue_navigator.graph_navigator import (
    EndpointNotFoundError,
    GraphNavigator,
    InvalidEdgeError,
    MissingEdgeEndpointError,
    StartVertexMissingError
)

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
    assert graph_navigator.get_current_vertex_text() == {"vertex_0": "Hello. You have 2 gold. Want to buy a flower?"}

# You can get current edge texts as {edge_name: edge.text}
def test_get_current_edge_texts(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.get_current_edge_texts() == {"edge_0": "Yes, I'll buy a flower.", "edge_3": "No thanks."}

# You can get all current turn text in one payload
def test_get_current_turn(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state)
    assert graph_navigator.get_current_turn() == {"vertex_text": {"vertex_0": "Hello. You have 2 gold. Want to buy a flower?"}, "edge_texts": {"edge_0": "Yes, I'll buy a flower.", "edge_3": "No thanks."}}

# Starting vertex effects are applied immediately during navigator init
def test_init_applies_vertex_0_effects(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Charlie", "vertices": {"vertex_0": {"text": "Start.", "effects": [{"type": "modify_value", "target": "player.gold", "delta": -1}]}}, "edges": {}}
    )
    assert mock_game_state.player.gold == 2
    GraphNavigator(graph, mock_game_state)
    assert mock_game_state.player.gold == 1

# When you get the text, it should calculate values based on game state context (e.g., "{player.gold}" becomes "0" if player.gold == 0)
def test_getting_text_should_dynamically_evaluate_based_on_gamestate(alice_graph, mock_game_state_with_no_gold):
    graph_navigator = GraphNavigator(alice_graph, mock_game_state_with_no_gold)
    assert graph_navigator.get_current_vertex_text()["vertex_0"] == "Hello. You have 0 gold. Want to buy a flower?"
    assert graph_navigator.get_current_edge_texts()["edge_2"] == "Well, can I buy one with 0 gold?"

# Validation that vertex_0 exists
def test_vertex_0_exists(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_1": {"text": "Orphaned.", "effects": []}}, "edges": {}}
    )
    with raises(StartVertexMissingError):
        GraphNavigator(graph, mock_game_state)

# Validation that no from_vertex/to_vertex is still set to "__MISSING__"
def test_no_missing_from_or_to_vertices(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start", "effects": []}}, "edges": {"edge_0": {"from": "vertex_0", "to": "__MISSING__", "text": "Missing target.", "predicates": [], "effects": []}}}
    )
    with raises(MissingEdgeEndpointError):
        GraphNavigator(graph, mock_game_state)

# Validation that every from_vertex/to_vertex str is actually in vertex_dict
def test_all_endpoints_exist_in_vertex_dict(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start", "effects": []}}, "edges": {"edge_0": {"from": "vertex_0", "to": "vertex_99", "text": "Missing target.", "predicates": [], "effects": []}}}
    )
    with raises(EndpointNotFoundError):
        GraphNavigator(graph, mock_game_state)

# Validation that every vertex is reachable from vertex_0
# Validation that aggregates all present validation errors to display at once