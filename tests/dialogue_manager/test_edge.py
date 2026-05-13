from fixtures import hello_world_graph

from dialogue_manager.edge import Edge
from dialogue_manager.vertex import Vertex

# The from_vertex and to_vertex attributes are Vertices
def test_from_and_to_are_vertices(hello_world_graph):
    for edge in hello_world_graph.edges:
        assert isinstance(edge.from_vertex, Vertex)
        assert isinstance(edge.to_vertex, Vertex)
