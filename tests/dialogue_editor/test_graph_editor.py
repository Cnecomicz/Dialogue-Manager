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
    graph_editor.add_effect("begin", "player.gold = player.gold-1")
    assert graph_editor.graph.vertex_dict["begin"] == Vertex(
        "begin", {"text": "Updated text.", "effects": [{"type": "modify_value", "target": "player.gold", "delta": -1},]}
    )

# You can add new edges
def test_add_new_edge():
    graph_editor = GraphEditor()
    graph_editor.add_vertex("begin", "Hello world.")
    graph_editor.add_vertex("end", "Goodbye world.")
    graph_editor.add_edge("begin", "end", "This is an edge.")
    assert len(graph_editor.graph.edge_dict) == 1
    assert graph_editor.graph.edge_dict["begin_to_end"] == Edge(
        "begin_to_end", {"from": "begin", "to": "end", "text": "This is an edge.", "predicates": [], "effects": []}
    )

# If you don't add a to_vertex when creating an edge it makes a new one

# You can edit existing edges

# You can remove an edge

# You can remove a vertex 

# Removing a vertex removes all connected edges too

# You can save the Graph to yaml