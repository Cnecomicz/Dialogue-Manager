from dialogue_editor.graph_editor import GraphEditor
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

# The adapter takes as input a Graph
def test_instantiating_adapter(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)

# The adapter turns Graph.vertex_dict into Cytoscape nodes
def test_cytoscape_nodes(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)
    assert {"data": {"id": "buy_flower", "label": "EFFECTS:\nplayer.inventory.append(Flower)\nalice.inventory.remove(Flower)\n\nTEXT:\nThanks. You now have {player.gold} gold. Want to buy another?"}} in cytoscape_adapter.nodes

# The adapter turns Graph.edge_dict into Cytoscape nodes with Cytoscape edges between them
def test_cytoscape_edges(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)
    assert len(cytoscape_adapter.nodes) == len(hello_world_graph.vertex_dict) + len(hello_world_graph.edge_dict)
    assert {"data": {"id": "vertex_0_to_buy_flower", "label": "TEXT:\nYes, I'll buy a flower.\n\nPREDICATES:\nplayer.gold >= 1\nFlower in alice.inventory\n\nEFFECTS:\nplayer.gold = player.gold-1", "is_edge_node": True}} in cytoscape_adapter.nodes
    assert len(cytoscape_adapter.edges) == 2*len(hello_world_graph.edge_dict)
    assert {"data": {"source": "vertex_0", "target": "vertex_0_to_buy_flower"}} in cytoscape_adapter.edges
    assert {"data": {"source": "vertex_0_to_buy_flower", "target": "buy_flower"}} in cytoscape_adapter.edges

# Unresolved endpoints are shown on edge nodes and invalid connectors are hidden
def test_cytoscape_unresolved_edge_after_non_cascade_delete():
    graph_editor = GraphEditor("data/hello_world.yaml")
    graph_editor.remove_vertex("vertex_0", cascade_delete=False)
    cytoscape_adapter = CytoscapeAdapter(graph_editor.graph)
    assert not any(
        edge["data"].get("source", "") == ""
        or edge["data"].get("target", "") == ""
        for edge in cytoscape_adapter.edges
    )
    unresolved_edge_nodes = [
        node for node in cytoscape_adapter.nodes
        if node["data"].get("is_edge_node")
        and node["data"].get("has_missing_endpoint")
    ]
    assert unresolved_edge_nodes
    assert any(
        "FROM: missing" in node["data"]["label"]
        or "TO: missing" in node["data"]["label"]
        for node in unresolved_edge_nodes
    )