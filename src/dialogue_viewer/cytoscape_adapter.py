from dialogue_model.graph import Graph

class CytoscapeAdapter:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph