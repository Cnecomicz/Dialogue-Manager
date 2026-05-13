from pytest import fixture

from dialogue_manager.graph import Graph

@fixture
def hello_world_graph():
    return Graph("data/hello_world.yaml")

@fixture
def mock_game_state_with_gold():
    class MockPlayer:
        def __init__(self):
            self.gold = 2
    class MockGameState:
        def __init__(self):
            self.player = MockPlayer()
    game_state = MockGameState()
    return game_state