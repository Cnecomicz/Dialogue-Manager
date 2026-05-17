from dialogue_viewer.graph_viewer import GraphViewer

# The GraphViewer takes in a Graph
def test_graph_viewer_creation(hello_world_graph):
    graph_viewer = GraphViewer(hello_world_graph)

# The GraphViewer spits out an image file
def test_dialogue_viewer_viewing(hello_world_graph):
    graph_viewer = GraphViewer(hello_world_graph)
    graph_viewer.render()