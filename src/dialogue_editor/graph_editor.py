from os import PathLike
from typing import Any
from yaml import safe_dump

from dialogue_editor.messages import (
    FIELD_SOURCE,
    FIELD_TARGET,
    FIELD_VERTEX,
    MSG_NO_YAML_PATH,
    MSG_VERTEX_CANNOT_BE_DELETED,
    MSG_VERTEX_NOT_FOUND
)
from dialogue_model.constants import (
    EDGE_PREFIX,
    MISSING_VERTEX,
    START_VERTEX,
    VERTEX_PREFIX
)
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph
from dialogue_model.vertex import Vertex

class VertexCannotBeDeletedError(Exception):
    """Raised when attempting to delete an ineligible vertex."""

    pass

class VertexNotFoundError(Exception):
    """Raised when a vertex identifier is not found in the graph."""

    def __init__(self, vertex_name: str, field_name: str | None = None) -> None:
        """Initialize the error with the offending vertex identifier and 
        field name.

        Args:
            vertex_name (str): Identifier that does not exist in vertex_dict.
            field_name (str | None): Reference to where the vertex is defined,
                such as "Source" or "Target".
        """
        self.vertex_name = vertex_name
        self.field_name = field_name
        field_label = field_name or FIELD_VERTEX
        super().__init__(
            MSG_VERTEX_NOT_FOUND.format(
                field_label=field_label, vertex_name=vertex_name
            )
        )

class GraphEditor:
    """Provide mutation and persistence helpers for a dialogue graph."""

    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        """Initialize an editor and optionally load an existing graph.

        Args:
            yaml_file (str | PathLike | None): yaml file path to load.
        """
        self.yaml_file = None
        self.graph = Graph()
        self.next_vertex_index = 0
        self.next_edge_index = 0
        if yaml_file is not None:
            self.load(yaml_file=yaml_file)

    def __repr__(self) -> str:
        """Return a debug representation of this editor.

        Returns:
            str: String representation of this editor.
        """
        return f'GraphEditor(yaml_file="{self.yaml_file}")'

    def __eq__(self, other: Any) -> bool:
        """Compare this editor with another object for graph equality.

        Args:
            other (Any): Object to compare against.

        Returns:
            bool: "True" when both editors contain equivalent graphs.
        """
        if not isinstance(other, GraphEditor):
            return NotImplemented
        return self.graph == other.graph

    def add_edge(
        self, 
        from_vertex: str, 
        to_vertex: str | None = None, 
        text: str | None = None, 
        predicates: list[dict[str, str | int]] | None = None, 
        effects: list[dict[str, str | int]] | None = None
    ) -> str:
        """Create and add a new edge to the graph.

        Args:
            from_vertex (str): Source vertex identifier.
            to_vertex (str | None): Target vertex identifier.
            text (str | None): Edge dialogue text.
            predicates (list[dict[str, str | int]] | None): Edge predicates.
            effects (list[dict[str, str | int]] | None): Edge effects.

        Returns:
            str: Identifier of the newly created edge.

        Raises:
            VertexNotFoundError: If from_vertex or to_vertex is not a valid
                vertex identifier.
        """
        self.require_valid_vertex(from_vertex, FIELD_SOURCE)
        if to_vertex is None:
            to_vertex = self.add_vertex()
        self.require_valid_vertex(to_vertex, FIELD_TARGET)
        if text is None:
            text = ""
        if predicates is None:
            predicates = []
        if effects is None:
            effects = []
        edge_name = f"{EDGE_PREFIX}{self.next_edge_index}"
        self.graph.edge_dict[edge_name] = Edge(
            edge_name, {
                "from": from_vertex,
                "to": to_vertex,
                "text": text,
                "predicates": predicates,
                "effects": effects
            }
        )
        self.next_edge_index += 1
        return edge_name

    def add_effect(
        self, vertex_or_edge_name: str, effect: dict[str, str | int]
    ) -> None:
        """Append an effect to a vertex or edge.

        Args:
            vertex_or_edge_name (str): Vertex or edge identifier.
            effect (dict[str, str | int]): Effect mapping to append.
        """
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.append(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.append(effect)

    def add_predicate(
        self, edge_name: str, predicate: dict[str, str | int]
    ) -> None:
        """Append a predicate to an edge.

        Args:
            edge_name (str): Edge identifier.
            predicate (dict[str, str | int]]): Predicate mapping to append.
        """
        self.graph.edge_dict[edge_name].predicates.append(predicate)

    def add_vertex(
        self, 
        text: str | None = None, 
        effects: list[dict[str, str | int]] | None = None
    ) -> str:
        """Create and add a new vertex to the graph.

        Args:
            text (str | None): Vertex dialogue text.
            effects (list[dict[str, str | int]] | None): Vertex effects.

        Returns:
            str: Identifier of the newly created vertex.
        """
        if text is None:
            text = ""
        if effects is None:
            effects = []
        vertex_name = f"{VERTEX_PREFIX}{self.next_vertex_index}"
        self.graph.vertex_dict[vertex_name] = Vertex(
            vertex_name, {"text": text, "effects": effects}
        )
        self.next_vertex_index += 1
        return vertex_name

    def edit_edge_effects(
        self, edge_name: str, effects: list[dict[str, str | int]]
    ) -> None:
        """Replace effects for an edge.

        Args:
            edge_name (str): Edge identifier.
            effects (list[dict[str, str | int]]): New effects list.
        """
        self.graph.edge_dict[edge_name].effects = effects

    def edit_edge_predicates(
        self, edge_name: str, predicates: list[dict[str, str | int]]
    ) -> None:
        """Replace predicates for an edge.

        Args:
            edge_name (str): Edge identifier.
            predicates (list[dict[str, str | int]]): New predicates list.
        """
        self.graph.edge_dict[edge_name].predicates = predicates

    def edit_edge_text(self, edge_name: str, text: str) -> None:
        """Replace the dialogue text for an edge.

        Args:
            edge_name (str): Edge identifier.
            text (str): New dialogue text.
        """
        self.graph.edge_dict[edge_name].text = text

    def edit_from_vertex(self, edge_name: str, from_vertex: str) -> None:
        """Replace the source vertex of an edge.

        Args:
            edge_name (str): Edge identifier.
            from_vertex (str): New source vertex identifier.

        Raises:
            VertexNotFoundError: If from_vertex is not a valid vertex
                identifier.
        """
        self.require_valid_vertex(from_vertex, FIELD_SOURCE)
        self.graph.edge_dict[edge_name].from_vertex = from_vertex

    def edit_name(self, name: str) -> None:
        """Replace the NPC name.

        Args:
            name (str): New NPC name.
        """
        self.graph.name = name

    def edit_to_vertex(self, edge_name: str, to_vertex: str) -> None:
        """Replace the target vertex of an edge.

        Args:
            edge_name (str): Edge identifier.
            to_vertex (str): New target vertex identifier.

        Raises:
            VertexNotFoundError: If to_vertex is not a valid vertex identifier.
        """
        self.require_valid_vertex(to_vertex, FIELD_TARGET)
        self.graph.edge_dict[edge_name].to_vertex = to_vertex

    def edit_vertex_effects(
        self, vertex_name: str, effects: list[dict[str, str | int]]
    ) -> None:
        """Replace effects for a vertex.

        Args:
            vertex_name (str): Vertex identifier.
            effects (list[dict[str, str | int]]): New effects list.
        """
        self.graph.vertex_dict[vertex_name].effects = effects

    def edit_vertex_text(self, vertex_name: str, text: str) -> None:
        """Replace the dialogue text for a vertex.

        Args:
            vertex_name (str): Vertex identifier.
            text (str): New dialogue text.
        """
        self.graph.vertex_dict[vertex_name].text = text

    def export_yaml_text(self) -> str:
        """Serialize the current graph to yaml text.

        Returns:
            str: yaml document string for the current graph.
        """
        yaml_data = {
            "name": self.graph.name,
            "vertices": {
                vertex_name: {
                    "text": vertex.text, 
                    "effects": vertex.effects
                }
                for vertex_name, vertex in self.graph.vertex_dict.items()
            },
            "edges": {
                edge_name: {
                    "from": edge.from_vertex,
                    "to": edge.to_vertex,
                    "text": edge.text,
                    "predicates": edge.predicates,
                    "effects": edge.effects
                }
                for edge_name, edge in self.graph.edge_dict.items()
            }
        }
        return safe_dump(yaml_data, sort_keys=False)

    def get_next_edge_index(self) -> int:
        """Compute the next available edge index.

        Returns:
            int: Next index to use for "edge_<index>" ids.
        """
        return self.get_next_index(self.graph.edge_dict, EDGE_PREFIX)

    def get_next_index(self, node_dict: dict[str, Any], prefix: str) -> int:
        """Compute the next numeric suffix for ids with a shared prefix.

        Args:
            node_dict (dict[str, Any]): Mapping containing identifier keys.
            prefix (str): Expected leading identifier prefix.

        Returns:
            int: Next available numeric suffix for matching keys.
        """
        if not node_dict:
            return 0
        indices = []
        for node_name in node_dict.keys():
            if not node_name.startswith(prefix):
                continue
            suffix = node_name.removeprefix(prefix)
            if suffix.isdigit():
                indices.append(int(suffix))
        return max(indices, default=len(node_dict)-1) + 1

    def get_next_vertex_index(self) -> int:
        """Compute the next available vertex index.

        Returns:
            int: Next index to use for "vertex_<index>" ids.
        """
        return self.get_next_index(self.graph.vertex_dict, VERTEX_PREFIX)

    def load(
        self, 
        yaml_file: str | PathLike | None = None, 
        yaml_data: dict | None = None
    ) -> None:
        """Load graph data from file and/or parsed yaml mapping.

        Args:
            yaml_file (str | PathLike | None): yaml file path to load.
            yaml_data (dict | None): Parsed yaml mapping.
        """
        self.yaml_file = yaml_file
        self.graph = Graph(yaml_file=yaml_file, yaml_data=yaml_data)
        self.next_vertex_index = self.get_next_vertex_index()
        self.next_edge_index = self.get_next_edge_index()

    def remove_edge(self, edge_name: str) -> None:
        """Remove an edge by identifier.

        Args:
            edge_name (str): Edge identifier.
        """
        del self.graph.edge_dict[edge_name]

    def remove_effect(
        self, vertex_or_edge_name: str, effect: dict[str, str | int]
    ) -> None:
        """Remove an effect from a vertex or edge.

        Args:
            vertex_or_edge_name (str): Vertex or edge identifier.
            effect (dict[str, str | int]): Effect mapping to remove.
        """
        if vertex_or_edge_name in self.graph.vertex_dict:
            self.graph.vertex_dict[vertex_or_edge_name].effects.remove(effect)
        elif vertex_or_edge_name in self.graph.edge_dict:
            self.graph.edge_dict[vertex_or_edge_name].effects.remove(effect)

    def remove_predicate(
        self, edge_name: str, predicate: dict[str, str | int]
    ) -> None:
        """Remove a predicate from an edge.

        Args:
            edge_name (str): Edge identifier.
            predicate (dict[str, str | int]): Predicate mapping to remove.
        """
        self.graph.edge_dict[edge_name].predicates.remove(predicate)

    def remove_vertex(
        self, vertex_name: str, cascade_delete: bool = False
    ) -> None:
        """Remove a vertex and optionally connected edges.

        Args:
            vertex_name (str): Vertex identifier.
            cascade_delete (bool): Removed connected edges when "True".

        Raises:
            VertexCannotBeDeletedError: If vertex_name is vertex_0.
        """
        if vertex_name == START_VERTEX:
            raise VertexCannotBeDeletedError(
                MSG_VERTEX_CANNOT_BE_DELETED.format(vertex_name=START_VERTEX)
            )
        if cascade_delete:
            edges_to_remove = [
                edge_name
                for edge_name, edge in self.graph.edge_dict.items()
                if edge.from_vertex == vertex_name
                or edge.to_vertex == vertex_name
            ]
            for edge_name in edges_to_remove:
                self.remove_edge(edge_name)
        for edge_name, edge in self.graph.edge_dict.items():
            if edge.from_vertex == vertex_name:
                self.edit_from_vertex(edge_name, MISSING_VERTEX)
            if edge.to_vertex == vertex_name:
                self.edit_to_vertex(edge_name, MISSING_VERTEX)
        del self.graph.vertex_dict[vertex_name]

    def require_valid_vertex(
        self, vertex_name: str, field_name: str | None = None
    ) -> None:
        """Raise VertexNotFoundError if vertex_name is not a valid reference.
        "__MISSING__" is treated as valid.

        Args:
            vertex_name (str): Vertex identifier to validate.
            field_name (str | None): Optional endpoint label used in the
                error message (for example, "Source" or "Target").

        Raises:
            VertexNotFoundError: If vertex_name is not in the graph and is not
                "__MISSING__".
        """
        if (
            vertex_name != MISSING_VERTEX
            and vertex_name not in self.graph.vertex_dict
        ):
            raise VertexNotFoundError(vertex_name, field_name)


    def save(self, yaml_file: str | PathLike | None = None) -> None:
        """Persist the current graph to a yaml file.

        Args:
            yaml_file (str | PathLike | None): Destination file path.

        Raises:
            ValueError: If no destination path is available.
        """
        if yaml_file is None:
            yaml_file = self.yaml_file
        if yaml_file is None:
            raise ValueError(MSG_NO_YAML_PATH)
        yaml_data = self.export_yaml_text()
        with open(yaml_file, "w") as f:
            f.write(yaml_data)
