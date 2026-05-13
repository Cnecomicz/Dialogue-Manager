from fixtures import hello_world_graph

from dialogue_manager.edge import Edge
from dialogue_manager.vertex import Vertex

# GraphBuilder reads the yaml and creates classes of vertices and edges
def test_creation_of_vertices_and_edges(hello_world_graph):
    assert len(hello_world_graph.vertices) == 4
    assert len(hello_world_graph.edges) == 6

# Vertices and edges are proper classes
def test_vertices_and_edges_are_classes(hello_world_graph):
    for vertex_name, vertex in hello_world_graph.vertices.items():
        assert isinstance(vertex, Vertex)
    for edge_name, edge in hello_world_graph.edges.items():
        assert isinstance(edge, Edge)
