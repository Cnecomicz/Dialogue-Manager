from pytest import raises

from dialogue_model.graph import Graph
from dialogue_navigator.graph_navigator import GraphNavigator, InvalidEdgeError
from dialogue_navigator.state_accessor import (
    AttributeStateAccessor, GameStatePathError
)
from dialogue_navigator.turn import Option, Turn

# GraphNavigator has a current vertex that starts with "begin"
def test_starting_current_vertex(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    assert graph_navigator.current_vertex == "vertex_0"

# GraphNavigator keeps track of valid edge choices for your current vertex
def test_has_valid_edges(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    assert len(graph_navigator.current_edges) == 2
    assert graph_navigator.current_edges == {
        "edge_0": alice_graph.edge_dict["edge_0"],
        "edge_3": alice_graph.edge_dict["edge_3"]
    }

# You can't select an edge if it's not valid
def test_error_when_selecting_invalid_edge(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    with raises(InvalidEdgeError):
        graph_navigator.select("edge_2")

# Selecting a valid edge causes its effects to occur
def test_select_edge_to_cause_effects(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    graph_navigator.select("edge_0")
    assert mock_game_state.player.gold == 1

# Selecting an edge updates your current vertex
def test_select_edge_to_go_to_next_vertex(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    graph_navigator.select("edge_0")
    assert graph_navigator.current_vertex == "vertex_1"

# If the game state changes mid conversation, the valid edges change to reflect that
def test_error_when_selecting_invalid_edge_that_was_previously_valid(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    graph_navigator.select("edge_0")
    graph_navigator.select("edge_4")
    with raises(InvalidEdgeError):
        graph_navigator.select("edge_4")

# Entering a vertex causes its effects to procure
def test_new_vertex_causes_effects(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    assert mock_game_state.player.inventory == []
    assert mock_game_state.alice.inventory == ["Flower", "Flower"]
    graph_navigator.select("edge_0")
    assert mock_game_state.player.inventory == ["Flower"]
    assert mock_game_state.alice.inventory == ["Flower"]

# Edge predicates can be ANDed
def test_edge_predicate_1_and_predicate_2(alice_graph, mock_game_state_with_limited_inventory):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state_with_limited_inventory)
    graph_navigator.select("edge_0")
    with raises(InvalidEdgeError):
        graph_navigator.select("buy_flower_to_buy_flower")
    graph_navigator.select("edge_5")

# You can get the current turn's vertex id and NPC line
def test_get_current_turn_vertex_and_text(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    turn = graph_navigator.get_current_turn()
    assert isinstance(turn, Turn)
    assert turn.vertex == "vertex_0"
    assert turn.text == "Hello. You have 2 gold. Want to buy a flower?"

# You can get the current turn's valid options
def test_get_current_turn_options(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    turn = graph_navigator.get_current_turn()
    assert turn.options == [
        Option(edge="edge_0", text="Yes, I'll buy a flower."), Option(edge="edge_3", text="No thanks.")
    ]

# A turn with available options is not over
def test_turn_not_over_when_options_remain(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    assert graph_navigator.get_current_turn().is_over is False

# And a turn with no available options is over
def test_turn_over_when_no_options_remain(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Charlie", "vertices": {"vertex_0": {"text": "Bye.", "effects": []}}, "edges": {}}
    )
    graph_navigator = GraphNavigator(graph, game_state=mock_game_state)
    turn = graph_navigator.get_current_turn()
    assert turn.options == []
    assert turn.is_over

# respond_with does what select and get_curent_turn do
def test_respond_with_returns_next_turn(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    assert graph_navigator.current_vertex == "vertex_0"
    assert mock_game_state.player.gold == 2
    turn = graph_navigator.respond_with("edge_0")
    assert graph_navigator.current_vertex == "vertex_1"
    assert turn.vertex == "vertex_1"
    assert mock_game_state.player.gold == 1

# You get an error if you try to pick an unselectable edge
def test_respond_with_invalid_edge(alice_graph, mock_game_state):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state)
    with raises(InvalidEdgeError):
        graph_navigator.respond_with("edge_2")

# Starting vertex effects are applied immediately during navigator init
def test_init_applies_vertex_0_effects(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Charlie", "vertices": {"vertex_0": {"text": "Start.", "effects": [{"type": "modify_value", "target": "player.gold", "delta": -1}]}}, "edges": {}}
    )
    assert mock_game_state.player.gold == 2
    GraphNavigator(graph, game_state=mock_game_state)
    assert mock_game_state.player.gold == 1

# When you get the text, it should calculate values based on game state context (e.g., "{player.gold}" becomes "0" if player.gold == 0)
def test_getting_text_should_dynamically_evaluate_based_on_gamestate(alice_graph, mock_game_state_with_no_gold):
    graph_navigator = GraphNavigator(alice_graph, game_state=mock_game_state_with_no_gold)
    turn = graph_navigator.get_current_turn()
    assert turn.text == "Hello. You have 0 gold. Want to buy a flower?"
    option_texts = {option.edge: option.text for option in turn.options}
    assert option_texts["edge_2"] == "Well, can I buy one with 0 gold?"

# You must provide exactly one of game_state or accessor
def test_need_either_game_state_or_accessor(alice_graph, mock_game_state):
    with raises(ValueError):
        GraphNavigator(alice_graph)
    with raises(ValueError):
        GraphNavigator(alice_graph, game_state=mock_game_state, accessor=AttributeStateAccessor(mock_game_state))
    success_1 = GraphNavigator(alice_graph, game_state=mock_game_state)
    success_2 = GraphNavigator(alice_graph, accessor=AttributeStateAccessor(mock_game_state))
    success_2.select("edge_0")
    assert mock_game_state.player.gold == 1

# Bad paths raise GameStatePathError
def test_unresolved_path_raises_error(mock_game_state):
    graph = Graph(
        yaml_data={"name": "Dana", "vertices": {"vertex_0": {"text": "Hi.", "effects": []}, "vertex_1": {"text": "Bye.", "effects": []}}, "edges": {"edge_0": {"from": "vertex_0", "to": "vertex_1", "text": "Leave.", "predicates": [{"type": "check_value", "path": "player.nonexistent", "op": ">=", "value": 1}], "effects": []}}}
    )
    graph_navigator = GraphNavigator(graph, game_state=mock_game_state)
    with raises(GameStatePathError) as error:
        graph_navigator.get_current_turn()
    assert "player.nonexistent" in str(error.value)
    assert error.value.missing_attr == "nonexistent"