class Vertex:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.text = data["text"]
        self.effects = data["effects"]