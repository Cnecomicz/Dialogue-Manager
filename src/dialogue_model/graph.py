from os import PathLike
from pathlib import Path
from typing import Any
from yaml import safe_load

from dialogue_model.edge import Edge
from dialogue_model.vertex import Vertex

class Graph:
    """Represent a dialogue graph loaded from yaml data.

    Attributes:
        yaml_file (str | PathLike | None): Source yaml path when loaded.
        name (str): NPC name.
        vertex_dict (dict[str, Vertex]): Vertex mapping by id.
        edge_dict (dict[str, Edge]): Edge mapping by id.
    """

    def __init__(
        self, 
        yaml_file: str | PathLike | None = None, 
        yaml_data: dict | None = None
    ) -> None:
        """Initialize a graph from file input or in-memory yaml mapping.

        Args:
            yaml_file (str | PathLike | None): Path to a yaml file.
            yaml_data (dict | None): Pre-parsed yaml mapping.
        """
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
        """Return a debug representation of this graph.

        Returns:
            str: String representation of this graph.
        """
        return f'Graph(yaml_file="{self.yaml_file}")'

    def __eq__(self, other: Any) -> bool:
        """Compare this graph with another object for value equality.

        Args:
            other (Any): Object to compare against.

        Returns:
            bool: "True" when graph name, vertices, and edges match.
        """
        if not isinstance(other, Graph):
            return NotImplemented
        return (
            self.name == other.name 
            and self.vertex_dict == other.vertex_dict 
            and self.edge_dict == other.edge_dict
        )

    def get_yaml(self, yaml_file: str | PathLike | None) -> dict:
        """Load yaml content from a file path.

        Args:
            yaml_file (str | PathLike | None): File path to load.

        Returns:
            dict: Parsed yaml mapping, or an empty dictionary when unavailable.
        """
        if yaml_file is None:
            return {}
        yaml_path = Path(yaml_file)
        if not yaml_path.exists():
            return {}
        with open(yaml_path, "r") as f:
            return safe_load(f) or {}

    def normalize_yaml(self, data: dict) -> dict:
        """Normalize yaml data to the expected graph schema.

        Args:
            data (dict): Raw yaml mapping.

        Returns:
            dict: Mapping with "name", "vertices", and "edges" keys.
        """
        return {
            "name": data.get("name", ""),
            "vertices": data.get("vertices") or {},
            "edges": data.get("edges") or {},
        }