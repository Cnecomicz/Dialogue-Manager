from dialogue_viewer.graph_viewer import GraphViewer

# The GraphViewer takes in a Graph
def test_graph_viewer_creation():
    graph_viewer = GraphViewer("data/alice_dialogue_graph.yaml")

# The GraphViewer spits out an image file
def test_dialogue_viewer_viewing():
    graph_viewer = GraphViewer("data/alice_dialogue_graph.yaml")
    graph_viewer.render()