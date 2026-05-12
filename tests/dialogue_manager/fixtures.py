from pytest import fixture

from dialogue_manager.graph import Graph

@fixture
def hello_world_graph():
    return Graph("data/hello_world.yaml")