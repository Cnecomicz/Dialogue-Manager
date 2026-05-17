from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

# The from_vertex and to_vertex attributes are Vertices
def test_from_and_to_are_vertices(hello_world_graph):
    for edge_name, edge in hello_world_graph.edge_dict.items():
        assert isinstance(edge.from_vertex, Vertex)
        assert isinstance(edge.to_vertex, Vertex)
