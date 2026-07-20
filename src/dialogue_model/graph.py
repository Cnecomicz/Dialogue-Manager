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
        yaml_data: dict | None = None,
        *,
        require_existing_file: bool = True
    ) -> None:
        """Initialize a graph from file input or in-memory yaml mapping.

        Args:
            yaml_file (str | PathLike | None): Path to a yaml file.
            yaml_data (dict | None): Pre-parsed yaml mapping.
            require_existing_file (bool): When True, a provided yaml_file
                that does not exist raises FileNotFoundError. When False,
                a missing file yields an empty graph.
        """
        self.yaml_file = yaml_file
        loaded_yaml_data = (
            yaml_data 
            if yaml_data is not None 
            else self.get_yaml(
                self.yaml_file, require_existing_file=require_existing_file
            )
        )
        normalized_data = self.normalize_yaml(loaded_yaml_data)
        self.name = normalized_data["name"]
        self.vertex_dict = {
            vertex_name: Vertex.from_dict(vertex_name, data)
            for vertex_name, data in normalized_data["vertices"].items()
        }
        self.edge_dict = {
            edge_name: Edge.from_dict(edge_name, data)
            for edge_name, data in normalized_data["edges"].items()
        }

    def __repr__(self) -> str:
        """Return a debug representation of this graph.

        Returns:
            str: String representation of this graph.
        """
        return (
            f"<Graph name={self.name!r} "
            f"vertices={len(self.vertex_dict)} edges={len(self.edge_dict)}>"
        )

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

    def get_yaml(
        self,
        yaml_file: str | PathLike | None,
        *,
        require_existing_file: bool = True
    ) -> dict:
        """Load yaml content from a file path.

        Args:
            yaml_file (str | PathLike | None): File path to load.
            require_existing_file (bool): When True, a provided path that
                does not exist raises FileNotFoundError; when False, it
                yields an empty mapping.

        Returns:
            dict: Parsed yaml mapping, or an empty dictionary when no path
                is given (or the path is missing and not required).

        Raises:
            FileNotFoundError: If a path is provided, does not exist, and
                require_existing_file is True.
        """
        if yaml_file is None:
            return {}
        yaml_path = Path(yaml_file)
        if not yaml_path.exists():
            if require_existing_file:
                raise FileNotFoundError(
                    f"Dialogue graph file not found: {yaml_file}"
                )
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