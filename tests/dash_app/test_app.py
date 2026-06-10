from base64 import b64encode
from pytest import raises

# The app can be created from an existing yaml graph
def test_creating_app_from_yaml(app):
    assert app.graph_editor.graph.name == "Alice"
    assert len(app.graph_editor.graph.vertex_dict) == 5
    assert len(app.graph_editor.graph.edge_dict) == 8
    assert app.get_filename(app.graph_editor.graph.name) == "alice_dialogue_graph.yaml"

# The app can turn the current graph into Cytoscape elements
def test_get_elements_from_graph(app):
    graph = app.graph_editor.graph
    elements = app.get_elements()
    assert len(elements) == len(graph.vertex_dict) + len(graph.edge_dict) + 2*len(graph.edge_dict)
    assert {"data": {"id": "vertex_0"}} in [
        {"data": {"id": element["data"]["id"]}} for element in elements if "id" in element["data"]
    ]

# Updating a vertex node changes the underlying graph
def test_update_vertex_node(app):
    new_effects = [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}]
    was_updated = app.update_node("vertex_0", "Edited vertex text.", [], new_effects)
    assert was_updated is True
    assert app.graph_editor.graph.vertex_dict["vertex_0"].text == "Edited vertex text."
    assert app.graph_editor.graph.vertex_dict["vertex_0"].effects == new_effects

# Updating an edge node changes the underlying graph
def test_update_edge_node(app):
    new_predicates = [{"type": "check_value", "path": "player.gold", "op": ">=", "value": 1}] 
    new_effects = [{"type": "modify_value", "target": "player.gold", "delta": -1}]
    was_updated = app.update_node("edge_0", "Edited edge text.", new_predicates, new_effects)
    assert was_updated is True
    assert app.graph_editor.graph.edge_dict["edge_0"].text == "Edited edge text."
    assert app.graph_editor.graph.edge_dict["edge_0"].predicates == new_predicates
    assert app.graph_editor.graph.edge_dict["edge_0"].effects == new_effects

# Updating an unknown node is rejected
def test_update_unknown_node_text(app):
    was_updated = app.update_node("not_a_node", "Edited text.", [], [])
    assert was_updated is False

# Adding a vertex creates a new graph vertex with the provided text and effects
def test_add_vertex_via_app(app):
    new_effects = [
        {"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}
    ]
    before_length = len(app.graph_editor.graph.vertex_dict)
    new_vertex_name = app.add_vertex("Brand new vertex.", new_effects)
    after_length = len(app.graph_editor.graph.vertex_dict)
    assert before_length + 1 == after_length
    assert new_vertex_name in app.graph_editor.graph.vertex_dict
    assert app.graph_editor.graph.vertex_dict[new_vertex_name].text == "Brand new vertex."
    assert app.graph_editor.graph.vertex_dict[new_vertex_name].effects == new_effects

# Adding a vertex appears in the Cytoscape elements
def test_added_vertex_appears_in_elements(app):
    new_vertex_name = app.add_vertex("Brand new vertex.")
    assert {"data": {"id": new_vertex_name, "label": "TEXT:\nBrand new vertex."}} in app.get_elements()

# Adding an edge creates a new graph edge with the provided from_vertex, to_vertex, text, predicates, and effects
def test_add_edge_via_app(app):
    new_predicates = [
        {"type": "check_value", "path": "player.gold", "op": "==", "value": 100}
    ]
    new_effects = [
        {"type": "modify_value", "target": "player.gold", "delta": 100}
    ]
    before_length = len(app.graph_editor.graph.edge_dict)
    new_edge_name = app.add_edge(
        "vertex_0", "vertex_1", "A new edge", new_predicates, new_effects
    )
    after_length = len(app.graph_editor.graph.edge_dict)
    assert before_length + 1 == after_length
    assert new_edge_name in app.graph_editor.graph.edge_dict
    assert app.graph_editor.graph.edge_dict[new_edge_name].text == "A new edge"
    assert app.graph_editor.graph.edge_dict[new_edge_name].predicates == new_predicates
    assert app.graph_editor.graph.edge_dict[new_edge_name].effects == new_effects

# Removing a selected edge removes it from the graph
def test_remove_edge_via_app(app):
    assert "edge_0" in app.graph_editor.graph.edge_dict
    was_removed = app.remove_node("edge_0")
    assert was_removed is True
    assert "edge_0" not in app.graph_editor.graph.edge_dict

# Removing a selected vertex without cascade keeps connected edges
def test_remove_vertex_without_cascade(app):
    app.graph_editor.add_edge("vertex_0", "vertex_1", "Temporary edge")
    edge_name = f"edge_{app.graph_editor.next_edge_index-1}"
    was_removed = app.remove_node("vertex_0", cascade_delete=False)
    assert "vertex_0" not in app.graph_editor.graph.vertex_dict
    assert edge_name in app.graph_editor.graph.edge_dict

# Removing a selected vertex with cascade removes selected edges
def test_remove_vertex_with_cascade(app):
    app.graph_editor.add_edge("vertex_0", "vertex_1", "Temporary edge")
    edge_name = f"edge_{app.graph_editor.next_edge_index-1}"
    was_removed = app.remove_node("vertex_0", cascade_delete=True)
    assert "vertex_0" not in app.graph_editor.graph.vertex_dict
    assert edge_name not in app.graph_editor.graph.edge_dict


# Cascade is disabled when edge is selected
def test_cascade_disabled_for_edges(app):
    selected_node_text, options, value = app.get_delete_section_state(
        [{"id": "edge_0"}], ["cascade"]
    )
    assert selected_node_text == "Selected node: edge_0"
    assert options == [{"label": "Cascade delete", "value": "cascade", "disabled": True}]
    assert value == []

# Cascade is enabled when vertex is selected
def test_cascade_enabled_for_vertices(app):
    selected_node_text, options, value = app.get_delete_section_state(
        [{"id": "vertex_0"}], ["cascade"]
    )
    assert selected_node_text == "Selected node: vertex_0"
    assert options == [{"label": "Cascade delete", "value": "cascade", "disabled": False}]
    assert value == ["cascade"]

# Editing an edge only saves from/to fields if they are valid
def test_update_edge_endpoints_does_not_save_invalid_endpoint(app):
    original_to = app.graph_editor.graph.edge_dict["edge_0"].to_vertex
    was_updated, warnings = app.update_edge_endpoints(
        "edge_0", "vertex_1", "not_a_vertex"
    )
    assert was_updated is True
    assert app.graph_editor.graph.edge_dict["edge_0"].from_vertex == "vertex_1"
    assert app.graph_editor.graph.edge_dict["edge_0"].to_vertex == original_to
    assert warnings == ["Invalid to vertex: not_a_vertex"]

# Unresolved count is based on how many fixes to be made
def test_count_unresolved_connections_for_vertex_delete(app):
    app.graph_editor.add_edge("vertex_0", "vertex_1", "Edge 1")
    app.graph_editor.add_edge("vertex_1", "vertex_0", "Edge 2")
    unresolved_count = app.count_unresolved_connections("vertex_0")
    assert unresolved_count >= 2

# Uploaded yaml can be decoded into dict data
def test_parse_uploaded_yaml(app):
    yaml_text = "name: Bob\nvertices: {}\nedges: {}\n"
    payload = "data:text/yaml;base64," + b64encode(yaml_text.encode("utf-8")).decode("ascii")
    parsed_data = app.parse_uploaded_yaml(payload)
    assert parsed_data["name"] == "Bob"
    assert parsed_data["vertices"] == {}
    assert parsed_data["edges"] == {}

# Error if file has invalid encoding
def test_parse_uploaded_yaml_invalid_encoding(app):
    with raises(ValueError, match="invalid file encoding"):
        app.parse_uploaded_yaml("data:text/yaml;base64,***")

# Error if yaml has invalid syntax
def test_parse_uploaded_yaml_invalid_syntax(app):
    invalid_yaml = "name: [Not terminated"
    payload = "data:text/yaml;base64," + b64encode(invalid_yaml.encode("utf-8")).decode("ascii")
    with raises(ValueError, match="invalid yaml format"):
        app.parse_uploaded_yaml(payload)

# Error if yaml doesn't at least start with the right format
def test_parse_uploaded_yaml_requires_mapping_root(app):
    list_yaml = "-one\n- two\n"
    payload = "data:text/yaml;base64," + b64encode(list_yaml.encode("utf-8")).decode("ascii")
    with raises(ValueError, match="root must be a dictionary"):
        app.parse_uploaded_yaml(payload)

# You can reupload the same file
def test_upload_reset_callback_registered(app):
    callback_key = "upload-graph.contents"
    assert callback_key in app.callback_map
    callback_inputs = app.callback_map[callback_key]["inputs"]
    assert {"id": "action-status", "property": "value"} in callback_inputs