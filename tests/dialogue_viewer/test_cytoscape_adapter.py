from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

# The adapter takes as input a Graph
def test_instantiating_adapter(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)

# The adapter turns Graph.vertex_dict into Cytoscape nodes
def test_cytoscape_nodes(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)
    assert len(cytoscape_adapter.nodes) == len(hello_world_graph.vertex_dict)
    assert {"data": {"id": "buy_flower", "label": "EFFECTS:\nplayer.inventory.append(Flower)\nalice.inventory.remove(Flower)\n\nTEXT:\nThanks. You now have {player.gold} gold. Want to buy another?"}} in cytoscape_adapter.nodes

# The adapter turns Graph.edge_dict into Cytoscape nodes with Cytoscape edges between them
def test_cytoscape_edges(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)
    assert len(cytoscape_adapter.edges) == 2*len(hello_world_graph.edge_dict)
    assert {"data": {"source": "vertex_0", "target": "vertex_0_to_buy_flower"}}, {"data": {"source": "vertex_0_to_buy_flower", "target": "buy_flower"}} in cytoscape_adapter.edges

# The Cytoscape nodes have all the text and data from the Graph vertices/edges

