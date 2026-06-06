# The app can be created from an existing yaml graph
def test_creating_app_from_yaml(app):
    assert app.graph_editor.graph.name == "Alice"
    assert len(app.graph_editor.graph.vertex_dict) == 5
    assert len(app.graph_editor.graph.edge_dict) == 8

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
    was_updated = app.update_node("vertex_0_to_buy_flower", "Edited edge text.", new_predicates, new_effects)
    assert was_updated is True
    assert app.graph_editor.graph.edge_dict["vertex_0_to_buy_flower"].text == "Edited edge text."
    assert app.graph_editor.graph.edge_dict["vertex_0_to_buy_flower"].predicates == new_predicates
    assert app.graph_editor.graph.edge_dict["vertex_0_to_buy_flower"].effects == new_effects

# Updating an unknown node is rejected
def test_update_unknown_node_text(app):
    was_updated = app.update_node_text("not_a_node", "Edited text.")
    assert was_updated is False

# Adding a vertex creates a new graph vertex with the provided text
def test_add_vertex_via_app(app):
    before_length = len(app.graph_editor.graph.vertex_dict)
    new_vertex_name = app.add_vertex("Brand new vertex.")
    after_length = len(app.graph_editor.graph.vertex_dict)
    assert before_length + 1 == after_length
    assert new_vertex_name in app.graph_editor.graph.vertex_dict
    assert app.graph_editor.graph.vertex_dict[new_vertex_name].text == "Brand new vertex."

# Adding a vertex appears in the Cytoscape elements
def test_added_vertex_appears_in_elements(app):
    new_vertex_name = app.add_vertex("Brand new vertex.")
    assert {"data": {"id": new_vertex_name, "label": "TEXT:\nBrand new vertex."}} in app.get_elements()
