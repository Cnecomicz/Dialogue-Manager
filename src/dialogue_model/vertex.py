class Vertex:
    def __init__(self, vertex_name: str, data: dict) -> None:
        self.vertex_name = vertex_name
        self.text = data["text"]
        self.effects = data["effects"]

    def __eq__(self, other):
        if not isinstance(other, Vertex):
            return NotImplemented
        return self.__dict__ == other.__dict__