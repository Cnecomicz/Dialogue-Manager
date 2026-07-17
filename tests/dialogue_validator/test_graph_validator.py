from pytest import raises

from dialogue_model.graph import Graph
from dialogue_validator.graph_validator import (
    AggregatedValidationErrors,
    DisconnectedGraphError,
    EndpointNotFoundError,
    MissingEdgeEndpointError,
    StartVertexMissingError,
    UnreachableVertexError,
    collect_validation_errors
)

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