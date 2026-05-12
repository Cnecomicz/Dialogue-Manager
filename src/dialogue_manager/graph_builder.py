from yaml import safe_load

class GraphBuilder:
    def __init__(self, yaml_file: str):
        with open(yaml_file, 'r') as f:
            yaml_data = safe_load(f)
        self.name = yaml_data["name"]
        self.vertices = yaml_data["vertices"]
        self.edges = yaml_data["edges"]