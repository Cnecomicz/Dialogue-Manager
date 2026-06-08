from os import PathLike
from pathlib import Path
from typing import Any
from yaml import safe_load

from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

class Graph:
    def __init__(
        self, 
        yaml_file: str | PathLike | None = None, 
        yaml_data: dict | None = None
    ) -> None:
        self.yaml_file = yaml_file
        loaded_yaml_data = (
            yaml_data 
            if yaml_data is not None 
            else self.get_yaml(self.yaml_file)
        )
        normalized_data = self.normalize_yaml(loaded_yaml_data)
        self.name = normalized_data["name"]
        self.vertex_dict = {
            vertex_name: Vertex(vertex_name, data)
            for vertex_name, data in normalized_data["vertices"].items()
        }
        self.edge_dict = {
            edge_name: Edge(edge_name, data)
            for edge_name, data in normalized_data["edges"].items()
        }

    def __repr__(self) -> str:
        return f'Graph(yaml_file="{self.yaml_file}")'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Graph):
            return NotImplemented
        return (
            self.name == other.name 
            and self.vertex_dict == other.vertex_dict 
            and self.edge_dict == other.edge_dict
        )

    def get_yaml(self, yaml_file: str | PathLike | None) -> dict:
        if yaml_file is None:
            return {}
        yaml_path = Path(yaml_file)
        if not yaml_path.exists():
            return {}
        with open(yaml_path, "r") as f:
            return safe_load(f) or {}

    def normalize_yaml(self, data: dict) -> dict:
        return {
            "name": data.get("name", ""),
            "vertices": data.get("vertices") or {},
            "edges": data.get("edges") or {},
        }