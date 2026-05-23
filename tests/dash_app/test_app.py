from dash_app.app import App

# The app can be created from an existing yaml graph
def test_creating_app_from_yaml():
    app = App("data/hello_world.yaml")
    assert app.graph_editor.graph.name == "Alice"
    assert len(app.graph_editor.graph.vertex_dict) == 5
    assert len(app.graph_editor.graph.edge_dict) == 8

# The app can turn the current graph into Cytoscape elements
def test_get_elements_from_graph():
    app = App("data/hello_world.yaml")
    graph = app.graph_editor.graph
    elements = app.get_elements()
    assert len(elements) == len(graph.vertex_dict) + len(graph.edge_dict) + 2*len(graph.edge_dict)
    assert {"data": {"id": "vertex_0"}} in [
        {"data": {"id": element["data"]["id"]}} for element in elements if "id" in element["data"]
    ]

# Updating a vertex node text changes the underlying graph
def test_update_vertex_node_text():
    app = App("data/hello_world.yaml")
    was_updated = app.update_node_text("vertex_0", "Edited vertex text.")
    assert was_updated is True
    assert app.graph_editor.graph.vertex_dict["vertex_0"].text == "Edited vertex text."

# Updating an edge node text changes the underlying graph
def test_update_edge_node_text():
    app = App("data/hello_world.yaml")
    was_updated = app.update_node_text("vertex_0_to_buy_flower", "Edited edge text.")
    assert was_updated is True
    assert app.graph_editor.graph.edge_dict["vertex_0_to_buy_flower"].text == "Edited edge text."

# Updating an unknown node is rejected
def test_update_unknown_node_text():
    app = App("data/hello_world.yaml")
    was_updated = app.update_node_text("not_a_node", "Edited text.")
    assert was_updated is False

# Adding a vertex creates a new graph vertex with the provided text
def test_add_vertex_via_app():
    app = App("data/hello_world.yaml")
    before_length = len(app.graph_editor.graph.vertex_dict)
    new_vertex_name = app.add_vertex("Brand new vertex.")
    after_length = len(app.graph_editor.graph.vertex_dict)
    assert before_length + 1 == after_length
    assert new_vertex_name in app.graph_editor.graph.vertex_dict
    assert app.graph_editor.graph.vertex_dict[new_vertex_name].text == "Brand new vertex."

# Adding a vertex appears in the Cytoscape elements
def test_added_vertex_appears_in_elements():
    app = App("data/hello_world.yaml")
    new_vertex_name = app.add_vertex("Brand new vertex.")
    assert {"data": {"id": new_vertex_name, "label": "TEXT:\nBrand new vertex."}} in app.get_elements()

    