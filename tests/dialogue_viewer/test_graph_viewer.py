from dialogue_viewer.graph_viewer import GraphViewer

# The GraphViewer takes in a Graph
def test_graph_viewer_creation(alice_graph):
    graph_viewer = GraphViewer(alice_graph)

# The GraphViewer spits out an image file
def test_dialogue_viewer_viewing(alice_graph):
    graph_viewer = GraphViewer(alice_graph)
    graph_viewer.render()