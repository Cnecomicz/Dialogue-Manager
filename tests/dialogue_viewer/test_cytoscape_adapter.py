from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

# The adapter takes as input a Graph
def test_instantiating_adapter(hello_world_graph):
    cytoscape_adapter = CytoscapeAdapter(hello_world_graph)

# The adapter turns Graph.vertex_dict into Cytoscape nodes

# The adapter turns Graph.edge_dict into Cytoscape nodes with Cytoscape edges between them

# The Cytoscape nodes have all the text and data from the Graph vertices/edges

