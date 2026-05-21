from dash_app.app import App

# The app has graph_editor and cytoscape_adapter
def test_app_views_and_edits_one_synchronized_graph(hello_world_graph):
    app = App("data/hello_world.yaml")
    assert len(app.cytoscape_adapter.edges) == 2*len(hello_world_graph.edge_dict)
    app.graph_editor.edit_vertex_text("vertex_0", "Edited text.")
    assert app.graph.vertex_dict["vertex_0"].text == "Edited text."