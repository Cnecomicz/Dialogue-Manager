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
    assert new_vertex_name == "vertex_5"
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
    assert new_edge_name == "edge_8"
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
    edge_name = app.graph_editor.add_edge("vertex_0", "vertex_1", "Temporary edge")
    was_removed = app.remove_node("vertex_1", cascade_delete=False)
    assert "vertex_1" not in app.graph_editor.graph.vertex_dict
    assert edge_name in app.graph_editor.graph.edge_dict

# Removing a selected vertex with cascade removes selected edges
def test_remove_vertex_with_cascade(app):
    edge_name = app.graph_editor.add_edge("vertex_0", "vertex_1", "Temporary edge")
    was_removed = app.remove_node("vertex_1", cascade_delete=True)
    assert "vertex_1" not in app.graph_editor.graph.vertex_dict
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
    assert warnings == ["Could not update Target for Player node \"edge_0\" because NPC node \"not_a_vertex\" does not exist. Enter an existing NPC node ID in Target and try again."]

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
    with raises(ValueError, match="upload data is invalid"):
        app.parse_uploaded_yaml("data:text/yaml;base64,***")

# Error if yaml has invalid syntax
def test_parse_uploaded_yaml_invalid_syntax(app):
    invalid_yaml = "name: [Not terminated"
    payload = "data:text/yaml;base64," + b64encode(invalid_yaml.encode("utf-8")).decode("ascii")
    with raises(ValueError, match="yaml format is invalid"):
        app.parse_uploaded_yaml(payload)

# Error if yaml doesn't at least start with the right format
def test_parse_uploaded_yaml_requires_mapping_root(app):
    list_yaml = "-one\n- two\n"
    payload = "data:text/yaml;base64," + b64encode(list_yaml.encode("utf-8")).decode("ascii")
    with raises(ValueError, match="top level must be a dictionary"):
        app.parse_uploaded_yaml(payload)

# You can reupload the same file
def test_upload_reset_callback_registered(app):
    callback_key = "upload-graph-container.children"
    assert callback_key in app.callback_map
    callback_inputs = app.callback_map[callback_key]["inputs"]
    assert {"id": "action-log", "property": "data"} in callback_inputs

# Opening the add or edit modals autofills the fields (no matter how many times you do it)
def test_add_edge_or_edit_autofill_uses_open_click_and_selected_state(app):
    matching_add_edge_callbacks = [
        callback
        for callback in app.callback_map.values()
        if {"id": "open-add-edge-modal", "property": "n_clicks"}
        in callback.get("inputs", [])
        and {"id": "dialogue-editor", "property": "selectedNodeData"}
        in callback.get("state", [])
    ]
    matching_edit_callbacks = [
        callback
        for callback in app.callback_map.values()
        if {"id": "open-edit-modal", "property": "n_clicks"}
        in callback.get("inputs", [])
        and {"id": "dialogue-editor", "property": "selectedNodeData"}
        in callback.get("state", [])
    ]
    assert matching_add_edge_callbacks
    assert matching_edit_callbacks

# No UI log validation is raised when valid graph is loaded/saved
def test_runtime_validation_warnings_are_empty_for_valid_graph(app):
    warnings = app.get_runtime_validation_warnings()
    assert warnings == []

# Validation is raised when invalid graph is loaded/saved
def test_runtime_validation_warnings_are_nonempty_for_invalid_graph(app):
    app.graph_editor.load(
        yaml_data={"name": "Error", "vertices": {"vertex_0": {"text": "Start.", "effects": []}, "vertex_1": {"text": "Disconnected.", "effects": []}}, "edges": {"edge_0": {"from": "vertex_0", "to": "__MISSING__", "text": "Missing target", "predicates": [], "effects": []}, "edge_1": {"from": "vertex_0", "to": "vertex_99", "text": "Missing target.", "predicates": [], "effects": []}}}
    )
    warnings = app.get_runtime_validation_warnings()
    assert warnings[0] == "Runtime validation found 4 issue(s):"
    assert any("__MISSING__" in warning for warning in warnings)
    assert any('unknown vertex "vertex_99"' in warning for warning in warnings)
    assert any('Vertex "vertex_1" is unreachable' in warning for warning in warnings)
    assert any("Found 2 connected components" in warning for warning in warnings)

# Add Player Dialogue button is disabled when vertex_dict is empty
def test_add_player_button_enabled_state(app):
    disabled, style, tooltip = app.get_add_player_button_state()
    assert disabled is False
    assert style["cursor"] == "pointer"
    assert tooltip == "Create a player choice linking two NPC nodes (P)"
    app.graph_editor.load(yaml_data={"name": "Empty", "vertices": {}, "edges": {}})
    disabled, style, tooltip = app.get_add_player_button_state()
    assert disabled is True
    assert style["cursor"] == "not-allowed"
    assert tooltip == "Create at least one NPC node first."

# When the bottom panel is open, you can still pan and zoom the graph
def test_graph_interaction_lock_callback_registered(app):
    callback_keys = app.callback_map.keys()
    matching_callbacks = [
        key
        for key in callback_keys
        if "dialogue-editor.autoungrabify" in key
        and "dialogue-editor.autounselectify" in key
    ]
    assert matching_callbacks
    callback = app.callback_map[matching_callbacks[0]]
    callback_inputs = callback["inputs"]
    assert {"id": "bottom-panel-visible", "property": "data"} in callback_inputs
    assert {"id": "pick-mode-active", "property": "data"} in callback_inputs

# When pick mode is open, the bottom panel is grayed out
def test_pick_mode_bottom_panel_graying_callback_registered(app):
    callback_keys = app.callback_map.keys()
    matching_callbacks = [
        key
        for key in callback_keys
        if key.startswith("bottom-panel.style@")
    ]
    assert matching_callbacks
    callback = app.callback_map[matching_callbacks[0]]
    callback_inputs = callback["inputs"]
    callback_state = callback["state"]
    assert {"id": "pick-mode-active", "property": "data"} in callback_inputs
    assert {"id": "bottom-panel", "property": "style"} in callback_state

# Undo history starts with a clean baseline
def test_history_initialized_with_single_snapshot(app):
    assert len(app.history) == 1
    assert app.history_cursor == 0
    assert app.clean_cursor == 0
    assert app.get_undo_redo_state() == {"can_undo": False, "can_redo": False}

# Actions are tracked in history when they change the underlying yaml
def test_record_history_captures_mutation(app):
    app.add_vertex("New vertex.")
    state = app.record_history([{"message": "Created NPC line"}], "vertex_5", "Alice")
    assert len(app.history) == 2
    assert app.history_cursor == 1
    assert state == {"can_undo": True, "can_redo": False}
    assert app.history[1]["label"] == "Created NPC line"
    assert app.history[1]["selected_node_id"] == "vertex_5"

# Actions are not tracked if they don't change the graph
def test_record_history_ignores_non_mutation(app):
    state = app.record_history([{"message": "Ready."}], None, "Alice")
    assert len(app.history) == 1
    assert app.history_cursor == 0
    assert state == {"can_undo": False, "can_redo": False}

# Restore snapshot to undo
def test_restore_snapshot_undoes_mutation(app):
    before_count = len(app.graph_editor.graph.vertex_dict)
    app.add_vertex("New vertex.")
    assert len(app.graph_editor.graph.vertex_dict) == before_count + 1
    app.record_history([{"message": "Created"}], None, "Alice")
    snapshot = app.restore_snapshot(app.history_cursor-1)
    assert len(app.graph_editor.graph.vertex_dict) == before_count
    assert app.history_cursor == 0
    assert snapshot["label"] == "Ready."

# Restore snapshot maintains next_*_index across snapshots
def test_restore_snapshot_restores_counters(app):
    app.add_vertex("New vertex.")
    app.record_history([{"message": "Created"}], None, "Alice")
    added_next_vertex_index = app.graph_editor.next_vertex_index
    app.restore_snapshot(0)
    assert app.graph_editor.next_vertex_index < added_next_vertex_index
    app.restore_snapshot(1)
    assert app.graph_editor.next_vertex_index == added_next_vertex_index
    app.add_edge("vertex_0", text="New edge.")
    app.record_history([{"message": "Created"}], None, "Alice")
    added_next_edge_index = app.graph_editor.next_edge_index
    app.restore_snapshot(0)
    assert app.graph_editor.next_edge_index < added_next_edge_index
    app.restore_snapshot(1)
    assert app.graph_editor.next_edge_index < added_next_edge_index
    app.restore_snapshot(2)
    assert app.graph_editor.next_edge_index == added_next_edge_index

# If you make a change with pending redos you lose them
def test_record_history_truncates_redo_tail(app):
    app.add_vertex("First vertex.")
    app.record_history([{"message": "Created first"}], None, "Alice")
    app.add_vertex("Second vertex.")
    app.record_history([{"message": "Created second"}], None, "Alice")
    app.restore_snapshot(1)
    app.add_vertex("New edit timeline branch.")
    state = app.record_history([{"message": "Created new"}], None, "Alice")
    assert len(app.history) == 3
    assert app.history_cursor == 2
    assert app.history[2]["label"] == "Created new"
    assert state == {"can_undo": True, "can_redo": False}

# There is a reset_history() method to be called for things like new/open
def test_reset_history_clears_history(app):
    app.add_vertex("New vertex.")
    app.record_history([{"message": "Created"}], None, "Alice")
    app.reset_history()
    assert len(app.history) == 1
    assert app.history_cursor == 0
    assert app.clean_cursor == 0

# There is a large upper bound on history length
def test_history_caps_length(app):
    for index in range(105):
        app.add_vertex(f"Vertex number {index}.")
        app.record_history([{"message": f"Created {index}"}], None, "Alice")
    assert len(app.history) == 100
    assert app.history_cursor == 99
    assert app.clean_cursor == -1

# Undo and redo actions are wired to action log and history stores
def test_undo_redo_callbacks_registered(app):
    undo_callbacks = [
        callback
        for callback in app.callback_map.values()
        if {"id": "redo-action", "property": "n_clicks"}
        in callback.get("inputs", [])
    ]
    redo_callbacks = [
        callback
        for callback in app.callback_map.values()
        if {"id": "redo-action", "property": "n_clicks"}
        in callback.get("inputs", [])
    ]
    assert undo_callbacks
    assert redo_callbacks
    state_key = "undo-redo-state.data"
    assert state_key in app.callback_map
    assert {"id": "action-log", "property": "data"} in app.callback_map[state_key]["inputs"]