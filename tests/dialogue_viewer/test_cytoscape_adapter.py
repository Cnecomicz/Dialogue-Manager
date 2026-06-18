from dialogue_editor.graph_editor import GraphEditor
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

# The adapter takes as input a Graph
def test_instantiating_adapter(alice_graph):
    cytoscape_adapter = CytoscapeAdapter(alice_graph)

# The adapter turns Graph.vertex_dict into Cytoscape nodes
def test_cytoscape_nodes(alice_graph):
    cytoscape_adapter = CytoscapeAdapter(alice_graph)
    assert {"data": {"id": "vertex_1", "label": "EFFECTS:\nplayer.inventory.append(Flower)\nalice.inventory.remove(Flower)\n\nTEXT:\nThanks. You now have {player.gold} gold. Want to buy another?"}} in cytoscape_adapter.nodes

# The adapter turns Graph.edge_dict into Cytoscape nodes with Cytoscape edges between them
def test_cytoscape_edges(alice_graph):
    cytoscape_adapter = CytoscapeAdapter(alice_graph)
    assert len(cytoscape_adapter.nodes) == len(alice_graph.vertex_dict) + len(alice_graph.edge_dict)
    assert {"data": {"id": "edge_0", "label": "TEXT:\nYes, I'll buy a flower.\n\nPREDICATES:\nplayer.gold >= 1\nFlower in alice.inventory\n\nEFFECTS:\nplayer.gold = player.gold-1", "is_edge_node": True, "has_missing_endpoint": False}} in cytoscape_adapter.nodes
    assert len(cytoscape_adapter.edges) == 2*len(alice_graph.edge_dict)
    assert {"data": {"source": "vertex_0", "target": "edge_0"}} in cytoscape_adapter.edges
    assert {"data": {"source": "edge_0", "target": "vertex_1"}} in cytoscape_adapter.edges

# Unresolved endpoints are shown on edge nodes and invalid connectors are hidden
def test_cytoscape_unresolved_edge_after_non_cascade_delete():
    graph_editor = GraphEditor("data/alice_dialogue_graph.yaml")
    graph_editor.remove_vertex("vertex_1", cascade_delete=False)
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