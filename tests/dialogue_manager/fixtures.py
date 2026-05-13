from pytest import fixture

from dialogue_manager.graph import Graph

@fixture
def hello_world_graph():
    return Graph("data/hello_world.yaml")

@fixture
def mock_game_state_with_gold():
    return