from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

# GraphBuilder reads the yaml and creates classes of vertices and edges
def test_creation_of_vertices_and_edges(alice_graph):
    assert len(alice_graph.vertex_dict) == 5
    assert len(alice_graph.edge_dict) == 8

# Vertices and edges are proper classes
def test_vertices_and_edges_are_classes(alice_graph):
    for vertex_name, vertex in alice_graph.vertex_dict.items():
        assert isinstance(vertex, Vertex)
    for edge_name, edge in alice_graph.edge_dict.items():
        assert isinstance(edge, Edge)
