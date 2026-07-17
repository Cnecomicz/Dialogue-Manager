from pytest import raises

from dialogue_model.graph import Graph
from dialogue_validator.graph_validator import (
    AggregatedValidationErrors,
    DisconnectedGraphError,
    EndpointNotFoundError,
    InvalidEffectError,
    InvalidPredicateError,
    MalformedPlaceholderError,
    MissingEdgeEndpointError,
    StartVertexMissingError,
    UnreachableVertexError,
    collect_validation_errors,
    validate
)

# No errors for a valid graph, errors for an invalid graph
def test_valid_graph_has_no_errors_and_invalid_graphs_do(alice_graph):
    invalid_graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_1": {"text": "Orphaned.", "effects": []}}, "edges": {}}
    )
    assert len(collect_validation_errors(invalid_graph)) > 0
    with raises(AggregatedValidationErrors):
        validate(invalid_graph)
    assert collect_validation_errors(alice_graph) == []
    assert validate(alice_graph) is None

# Validation that vertex_0 exists
def test_vertex_0_exists():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_1": {"text": "Orphaned.", "effects": []}}, "edges": {}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, StartVertexMissingError) for error in errors)

# Validation that no from_vertex/to_vertex is still set to "__MISSING__"
def test_no_missing_from_or_to_vertices():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": []}}, "edges": {"edge_0": {"from": "vertex_0", "to": "__MISSING__", "text": "Missing target.", "predicates": [], "effects": []}}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, MissingEdgeEndpointError) for error in errors)

# Validation that every from_vertex/to_vertex str is actually in vertex_dict
def test_all_endpoints_exist_in_vertex_dict():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": []}}, "edges": {"edge_0": {"from": "vertex_0", "to": "vertex_99", "text": "Missing target.", "predicates": [], "effects": []}}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, EndpointNotFoundError) for error in errors)

# Validation that every vertex is reachable from vertex_0
def test_directed_connectivity_of_graph_starting_at_vertex_0():
    graph_1 = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": []}, "vertex_1": {"text": "Disconnected.", "effects": []}}, "edges": {}}
    )
    errors_1 = collect_validation_errors(graph_1)
    assert any(isinstance(error, UnreachableVertexError) for error in errors_1)
    graph_2 = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": []}, "vertex_1": {"text": "Connected, but in the wrong direction.", "effects": []}}, "edges": {"edge_0": {"from": "vertex_1", "to": "vertex_0", "text": "This sole edge ensures that in this graph, vertex_1 is not reachable FROM vertex_0.", "predicates": [], "effects": []}}}
    )
    errors_2 = collect_validation_errors(graph_2)
    assert any(isinstance(error, UnreachableVertexError) for error in errors_2)

# Validation that if vertex_0 is absent, graph is still (weakly) connected
def test_connectivity_in_absence_of_vertex_0():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_1": {"text": "1", "effects": []}, "vertex_2": {"text": "2", "effects": []}, "vertex_3": {"text": "3", "effects": []}, "vertex_4": {"text": "4", "effects": []}}, "edges": {"edge_0": {"from": "vertex_1", "to": "vertex_2", "text": "1-2", "predicates": [], "effects": []}, "edge_1": {"from": "vertex_3", "to": "vertex_4", "text": "3-4", "predicates": [], "effects": []}}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, DisconnectedGraphError) for error in errors)

# Validation that aggregates all present validation errors to display at once
def test_aggregate_multiple_validations():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_1": {"text": "Orphaned.", "effects": []}, "vertex_2": {"text": "Also orphaned.", "effects": []}}, "edges": {"edge_0": {"from": "vertex_1", "to": "__MISSING__", "text": "Missing target.", "predicates": [], "effects": []}, "edge_1": {"from": "vertex_1", "to": "vertex_99", "text": "Missing target.", "predicates": [], "effects": []}}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, StartVertexMissingError) for error in errors)
    assert any(isinstance(error, MissingEdgeEndpointError) for error in errors)
    assert any(isinstance(error, EndpointNotFoundError) for error in errors)
    assert any(isinstance(error, DisconnectedGraphError) for error in errors)
    assert len(errors) == 4

# Validation that effect/predicate types are legitimate
def test_unknown_effect_or_predicate_type():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": [{"type": "explode", "target": "player.gold", "delta": 1}]}}, "edges": {"edge_0": {"from": "vertex_0", "to": "vertex_0", "text": "Go.", "predicates": [{"type": "check_mood", "path": "player.mood", "op": "==", "value": "happy"}], "effects": []}}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, InvalidEffectError) for error in errors)
    assert any(isinstance(error, InvalidPredicateError) for error in errors)

# Validation that effect or predicate key is missing
def test_missing_effect_or_predicate_key():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": [{"type": "modify_value", "target": "player.gold"}]}}, "edges": {"edge_0": {"from": "vertex_0", "to": "vertex_0", "text": "Go.", "predicates": [{"type": "check_value", "path": "player.gold"}], "effects": []}}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, InvalidEffectError) for error in errors)
    assert any(isinstance(error, InvalidPredicateError) for error in errors)

# Validation that list methods are legitimate
def test_unknown_list_method():
    graph = Graph(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": [{"type": "modify_list", "target": "player.inventory", "method": "destroy", "value": "Box"}]}}, "effects": {}, "edges": {}}
    )
    errors = collect_validation_errors(graph)
    assert any(isinstance(error, InvalidEffectError) for error in errors)

# Validation that braces properly lint
def test_malformed_placeholder_braces():
    def make_graph_with_text(text: str) -> Graph:
        return Graph(
            yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": text, "effects": []}}, "edges": {}}
        )
    graph_1 = make_graph_with_text("You have {player.gold gold.")
    graph_2 = make_graph_with_text("You have player.gold} gold.")
    graph_3 = make_graph_with_text("You have {player.{gold}} gold.")
    graph_4 = make_graph_with_text("You have {} gold.")
    graph_5 = make_graph_with_text("You have {player.gold} gold.")
    errors_1 = collect_validation_errors(graph_1)
    errors_2 = collect_validation_errors(graph_2)
    errors_3 = collect_validation_errors(graph_3)
    errors_4 = collect_validation_errors(graph_4)
    errors_5 = collect_validation_errors(graph_5)
    assert any(isinstance(error, MalformedPlaceholderError) for error in errors_1)
    assert any(isinstance(error, MalformedPlaceholderError) for error in errors_2)
    assert any(isinstance(error, MalformedPlaceholderError) for error in errors_3)
    assert any(isinstance(error, MalformedPlaceholderError) for error in errors_4)
    assert not any(isinstance(error, MalformedPlaceholderError) for error in errors_5)