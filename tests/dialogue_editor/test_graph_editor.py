from dialogue_editor.graph_editor import GraphEditor

# You can load an existing yaml
def test_loading_graph(hello_world_graph):
    graph_editor = GraphEditor(hello_world_graph)
    assert graph_editor.graph.name == "Alice"
    assert len(graph_editor.graph.vertex_dict) == 5
    assert len(graph_editor.graph.edge_dict) == 8

# But loading is optional and if not passed in you start a new file

# You can add new vertices

# You can edit existing vertices

# You can add new edges

# You can edit existing edges

# You can remove an edge

# You can remove a vertex 

# Removing a vertex removes all connected edges too

# You can save the Graph to yaml