from fixtures import hello_world_graph

from dialogue_viewer.dialogue_viewer import DialogueViewer

# The DialogueViewer takes in a Graph
def test_dialogue_viewer_creation(hello_world_graph):
    dialogue_viewer = DialogueViewer(hello_world_graph)