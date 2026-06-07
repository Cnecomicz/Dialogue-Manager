from yaml import safe_load

from dialogue_editor.graph_editor import GraphEditor
from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

# You can load an existing yaml
def test_loading_graph():
    graph_editor = GraphEditor("data/hello_world.yaml")
    assert graph_editor.graph.name == "Alice"
    assert len(graph_editor.graph.vertex_dict) == 5
    assert len(graph_editor.graph.edge_dict) == 8

# But loading is optional and if not passed in you start a new file
def test_not_loading_graph():
    graph_editor = GraphEditor()
    assert graph_editor.graph.name == ""
    assert len(graph_editor.graph.vertex_dict) == 0
    assert len(graph_editor.graph.edge_dict) == 0

# You can add new vertices
def test_add_new_vertex():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    assert len(graph_editor.graph.vertex_dict) == 1
    assert graph_editor.graph.vertex_dict["vertex_0"] == Vertex(
        "vertex_0", {"text": "Hello world.", "effects": []}
    )

# You can edit existing vertices (removing/adding effects)
def test_editing_vertex():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.", [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}])
    graph_editor.edit_vertex_text("vertex_0", "Updated text.")
    graph_editor.remove_effect("vertex_0", {"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"})
    graph_editor.add_effect("vertex_0", {"type": "modify_value", "target": "player.gold", "delta": -1})
    assert graph_editor.graph.vertex_dict["vertex_0"] == Vertex(
        "vertex_0", {"text": "Updated text.", "effects": [{"type": "modify_value", "target": "player.gold", "delta": -1},]}
    )

# You can edit existing vertices (directly changing effects)
def test_editing_vertex_effects():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    new_effects = [
        {"type": "modify_value", "target": "player.gold", "delta": -1}
    ]
    graph_editor.edit_vertex_effects("vertex_0", new_effects)
    assert graph_editor.graph.vertex_dict["vertex_0"].effects == new_effects

# You can add new edges
def test_add_new_edge():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_vertex("Goodbye world.")
    graph_editor.add_edge("vertex_0", to_vertex="vertex_1", text="This is an edge.")
    assert len(graph_editor.graph.edge_dict) == 1
    assert graph_editor.graph.edge_dict["edge_0"] == Edge(
        "edge_0", {"from": "vertex_0", "to": "vertex_1", "text": "This is an edge.", "predicates": [], "effects": []}
    )

# If you don't add a to_vertex when creating an edge it makes a new one
def test_add_new_edge_without_to_vertex():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_edge("vertex_0", text="This is an edge without preexisting target.")
    assert len(graph_editor.graph.edge_dict) == 1
    assert len(graph_editor.graph.vertex_dict) == 2

# You can edit existing edges (removing/adding predicates/effects)
def test_editing_edge():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_vertex("Goodbye world.")
    graph_editor.add_edge("vertex_0", "vertex_1", "This is an edge.", [{"type": "check_value", "path": "player.gold", "op": ">=", "value": 1}], [{"type": "modify_value", "target": "player.gold", "delta": -1}])
    graph_editor.edit_from_vertex("edge_0", "vertex_1")
    graph_editor.edit_to_vertex("edge_0", "vertex_0")
    graph_editor.edit_edge_text("edge_0", "Updated text.")
    graph_editor.remove_predicate("edge_0", {"type": "check_value", "path": "player.gold", "op": ">=", "value": 1})
    graph_editor.add_predicate("edge_0", {"type": "check_list", "path": "player.inventory", "op": "not in", "value": "Bomb"})
    graph_editor.remove_effect("edge_0", {"type": "modify_value", "target": "player.gold", "delta": -1})
    graph_editor.add_effect("edge_0", {"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Bomb"})
    assert graph_editor.graph.edge_dict["edge_0"] == Edge(
        "edge_0", {"from": "vertex_1", "to": "vertex_0", "text": "Updated text.", "predicates": [{"type": "check_list", "path": "player.inventory", "op": "not in", "value": "Bomb"},], "effects": [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Bomb"}]}
    )

# You can edit existing edges (directly changing predicates/effects)
def test_editing_edge_predicates_and_effects():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_vertex("Goodbye world.")
    graph_editor.add_edge("vertex_0", "vertex_1", "This is an edge.")
    new_predicates = [
        {"type": "check_value", "path": "player.gold", "op": ">=", "value": 1}
    ]
    new_effects = [
        {"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}
    ]
    graph_editor.edit_edge_predicates("edge_0", new_predicates)
    graph_editor.edit_edge_effects("edge_0", new_effects)
    assert graph_editor.graph.edge_dict["edge_0"].predicates == new_predicates
    assert graph_editor.graph.edge_dict["edge_0"].effects == new_effects

# You can remove an edge
def test_removing_edge():
    graph_editor = GraphEditor()
    assert len(graph_editor.graph.vertex_dict) == 0
    assert len(graph_editor.graph.edge_dict) == 0
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_edge("vertex_0", text="This is an edge.")
    assert len(graph_editor.graph.vertex_dict) == 2
    assert len(graph_editor.graph.edge_dict) == 1
    graph_editor.remove_edge("edge_0")
    assert len(graph_editor.graph.vertex_dict) == 2
    assert len(graph_editor.graph.edge_dict) == 0

# You can remove a vertex 
def test_removing_vertex():
    graph_editor = GraphEditor()
    assert len(graph_editor.graph.vertex_dict) == 0
    graph_editor.add_vertex("Hello world.")
    assert len(graph_editor.graph.vertex_dict) == 1
    graph_editor.remove_vertex("vertex_0")
    assert len(graph_editor.graph.vertex_dict) == 0

# Removing a vertex removes the reference in all connected edges
def test_removing_connected_vertex():
    graph_editor = GraphEditor()
    assert len(graph_editor.graph.vertex_dict) == 0
    assert len(graph_editor.graph.edge_dict) == 0
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_edge("vertex_0", text="This is an edge.")
    assert len(graph_editor.graph.vertex_dict) == 2
    assert len(graph_editor.graph.edge_dict) == 1
    graph_editor.remove_vertex("vertex_0")
    assert len(graph_editor.graph.vertex_dict) == 1
    assert len(graph_editor.graph.edge_dict) == 1
    assert graph_editor.graph.edge_dict["edge_0"].from_vertex == "__MISSING__"

# Optionally, removing a vertex can remove all connected edges
def test_removing_connected_vertex_cascade_delete():
    graph_editor = GraphEditor()
    assert len(graph_editor.graph.vertex_dict) == 0
    assert len(graph_editor.graph.edge_dict) == 0
    graph_editor.add_vertex("Hello world.")
    graph_editor.add_edge("vertex_0", text="This is an edge.")
    assert len(graph_editor.graph.vertex_dict) == 2
    assert len(graph_editor.graph.edge_dict) == 1
    graph_editor.remove_vertex("vertex_0", True)
    assert len(graph_editor.graph.vertex_dict) == 1
    assert len(graph_editor.graph.edge_dict) == 0

# You can edit the NPC name
def test_edit_name():
    graph_editor = GraphEditor()
    graph_editor.edit_name("Bob")
    assert graph_editor.graph.name == "Bob"

# You can save the Graph to yaml
def test_save_to_yaml(tmp_path):
    yaml_file = tmp_path / "save_test.yaml"
    graph_editor = GraphEditor(yaml_file)
    graph_editor.edit_name("Bob")
    graph_editor.add_vertex("Hello world.", [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}])
    graph_editor.add_vertex("Goodbye world.", [{"type": "modify_value", "target": "player.name", "value": "Bob"}])
    graph_editor.add_edge("vertex_0", "vertex_1", "This is an edge.", [{"type": "check_value", "path": "player.gold", "op": ">=", "value": 1}], [{"type": "modify_value", "target": "player.gold", "delta": -1}])
    graph_editor.save()
    with open(yaml_file, "r") as f:
        yaml_data = safe_load(f)
    assert "name" in yaml_data
    assert "vertices" in yaml_data
    assert "edges" in yaml_data
    assert yaml_data["name"] == "Bob"
    assert yaml_data["vertices"] == {
        "vertex_0": {"text": "Hello world.", "effects": [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}]},
        "vertex_1": {"text": "Goodbye world.", "effects":[{"type": "modify_value", "target": "player.name", "value": "Bob"}]}
    }
    assert yaml_data["edges"] == {
        "edge_0": {"from": "vertex_0", "to": "vertex_1", "text": "This is an edge.", "predicates": [{"type": "check_value", "path": "player.gold", "op": ">=", "value": 1}], "effects": [{"type": "modify_value", "target": "player.gold", "delta": -1}]}
    }

# You can Save As if you pass an argument to save()
def test_save_as(tmp_path):
    graph_editor = GraphEditor()
    graph_editor.add_vertex("Hello world.")
    yaml_file = tmp_path / "save_as_test.yaml"
    graph_editor.save(yaml_file)
    with open(yaml_file, "r") as f:
        yaml_data = safe_load(f)
    assert "name" in yaml_data
    assert "vertices" in yaml_data
    assert "edges" in yaml_data
    assert yaml_data["name"] == ""
    assert yaml_data["vertices"] == {
        "vertex_0": {"text": "Hello world.", "effects": []}
    }
    assert yaml_data["edges"] == {}

# Testing round trip save and load
def test_save_load_round_trip(tmp_path):
    graph_editor_1 = GraphEditor()
    graph_editor_1.edit_name("Bob")
    graph_editor_1.add_vertex("Hello world.", [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"}])
    graph_editor_1.add_vertex("Goodbye world.", [{"type": "modify_value", "target": "player.name", "value": "Bob"}])
    graph_editor_1.add_edge("vertex_0", "vertex_1", "This is an edge.", [{"type": "check_value", "path": "player.gold", "op": ">=", "value": 1}], [{"type": "modify_value", "target": "player.gold", "delta": -1}])
    yaml_file = tmp_path / "round_trip_test.yaml"
    graph_editor_1.save(yaml_file)
    graph_editor_2 = GraphEditor(yaml_file)
    assert graph_editor_1 == graph_editor_2