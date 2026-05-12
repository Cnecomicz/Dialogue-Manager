from dialogue_manager.graph_builder import GraphBuilder

# GraphBuilder reads the yaml and creates classes of vertices and edges
def test_creation_of_vertices_and_edges():
    graph = GraphBuilder("data/hello_world.yaml")
    assert len(graph.vertices) == 4
    assert len(graph.edges) == 6