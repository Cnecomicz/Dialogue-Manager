from dialogue_editor.graph_editor import GraphEditor
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
    graph_editor.add_vertex("begin", "Hello world.")
    assert len(graph_editor.graph.vertex_dict) == 1
    assert graph_editor.graph.vertex_dict["begin"] == Vertex(
        "begin", {"text": "Hello world.", "effects": []}
    )

# You can edit existing vertices
def test_editing_vertex():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("begin", "Hello world.", [{"type": "modify_list", "target": "player.inventory", "method": "append", "value": "Flower"},])
    graph_editor.edit_vertex_text("begin", "Updated text.")
    graph_editor.remove_effect("begin", "player.inventory.append(Flower)")
    graph_editor.add_effect("begin", "player.inventory.remove(Flower)")
    assert graph_editor.graph.vertex_dict["begin"] == Vertex(
        "begin", {"text": "Updated text.", "effects": [{"type": "modify_list", "target": "player.inventory", "method": "remove", "value": "Flower"},]}
    )

# You can add new edges

# You can edit existing edges

# You can remove an edge

# You can remove a vertex 

# Removing a vertex removes all connected edges too

# You can save the Graph to yaml