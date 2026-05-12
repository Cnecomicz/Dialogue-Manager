class Edge:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.from_vertex = data["from"]
        self.to_vertex = data["to"]
        self.text = data["text"]
        self.filters = data["filters"]
        self.effects = data["effects"]