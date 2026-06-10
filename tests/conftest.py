from pytest import fixture

from dash_app.app import App
from dialogue_model.graph import Graph

@fixture
def app():
    return App("data/alice_dialogue_graph.yaml")

@fixture
def alice_graph():
    return Graph("data/alice_dialogue_graph.yaml")

@fixture
def mock_game_state():
    class MockPlayer:
        def __init__(self):
            self.gold = 2
            self.inventory = []
    class MockAlice:
        def __init__(self):
            self.inventory = ["Flower", "Flower"]
    class MockGameState:
        def __init__(self):
            self.player = MockPlayer()
            self.alice = MockAlice()
    game_state = MockGameState()
    return game_state

@fixture
def mock_game_state_with_limited_inventory():
    class MockPlayer:
        def __init__(self):
            self.gold = 2
            self.inventory = []
    class MockAlice:
        def __init__(self):
            self.inventory = ["Flower",]
    class MockGameState:
        def __init__(self):
            self.player = MockPlayer()
            self.alice = MockAlice()
    game_state = MockGameState()
    return game_state