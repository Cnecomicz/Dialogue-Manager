from dialogue_model.graph import Graph

class GraphEditor:
    def __init__(self, yaml_file: str = "") -> None:
        self.graph = Graph(yaml_file)