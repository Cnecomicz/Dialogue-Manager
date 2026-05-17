from dialogue_models.edge import Edge
from dialogue_models.vertex import Vertex

# GraphBuilder reads the yaml and creates classes of vertices and edges
def test_creation_of_vertices_and_edges(hello_world_graph):
    assert len(hello_world_graph.vertex_dict) == 5
    assert len(hello_world_graph.edge_dict) == 8

# Vertices and edges are proper classes
def test_vertices_and_edges_are_classes(hello_world_graph):
    for vertex_name, vertex in hello_world_graph.vertex_dict.items():
        assert isinstance(vertex, Vertex)
    for edge_name, edge in hello_world_graph.edge_dict.items():
        assert isinstance(edge, Edge)
