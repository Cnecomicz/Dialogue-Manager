from dialogue_navigator.helper_functions import (
    get_operator, get_nested_attr, set_nested_attr
)
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph

class InvalidEdgeError(Exception):
    """Raised when a selected edge is not valid for the current state."""

    pass

class GraphNavigator:
    """Navigate a dialogue graph using predicates and effects."""

    def __init__(self, graph: Graph, game_state: "GameState") -> None:
        """Initialize a navigator at the default starting vertex.

        Args:
            graph (Graph): Dialogue graph to navigate.
            game_state (GameState): Mutable game state object.
        """
        self.graph = graph
        self.game_state = game_state
        self.enter_vertex("vertex_0")

    @property
    def current_edges(self) -> dict[str, Edge]:
        """Return currently selectable outgoing edges.

        Returns:
            dict[str, Edge]: Edge mapping available from the current vertex.
        """
        current_edges = {}
        for edge_name, edge in self.graph.edge_dict.items():
            if (edge.from_vertex == self.current_vertex 
            and self.evaluate_edge_predicates(edge_name)):
                current_edges[edge_name] = edge
        return current_edges

    def enter_vertex(self, vertex_name: str) -> None:
        """Enter a vertex and apply all vertex effects.

        Args:
            vertex_name (str): Vertex identifier to enter.
        """
        vertex = self.graph.vertex_dict[vertex_name]
        for effect in vertex.effects:
            self.proc_effect(effect)
        self.current_vertex = vertex_name

    def evaluate_edge_predicates(self, edge_name: str) -> bool:
        """Evaluate whether all predicates for an edge pass.

        Args:
            edge_name (str): Edge identifier to evaluate.

        Returns:
            bool: "True" when every predicate is satisified.
        """
        edge = self.graph.edge_dict[edge_name]
        is_valid_edge = True
        for predicate in edge.predicates:
            match predicate["type"]:
                case "check_value":
                    operator_function = get_operator(predicate["op"])
                    current_value = get_nested_attr(
                        self.game_state, predicate["path"]
                    )
                    predicate_value = predicate["value"]
                    if not(operator_function(current_value, predicate_value)):
                        is_valid_edge = False
                case "check_list":
                    operator_function = get_operator(predicate["op"])
                    current_list = get_nested_attr(
                        self.game_state, predicate["path"]
                    )
                    predicate_value = predicate["value"]
                    if not(operator_function(predicate_value, current_list)):
                        is_valid_edge = False
        return is_valid_edge

    def get_current_edges(self) -> list[str]:
        """Return identifiers of currently selectable edges.

        Returns:
            list[str]: Edge identifiers from "self.current_edges".
        """
        return list(self.current_edges.keys())

    def get_current_edge_texts(self) -> dict[str, str]:
        """Return current selectable edge text keyed by edge_id.

        Returns:
            dict[str, str]: Mapping of edge_id to edge dialogue text.
        """
        return {
            edge_id: edge.text for edge_id, edge in self.current_edges.items()
        }

    def get_current_turn(self) -> dict[str, str | dict[str, str]]:
        """Return current turn text payload for game UI handshakes.

        Returns:
            dict[str, str | dict[str, str]]: Mapping containing current
            vertex dialogue text and available edge text options.
        """
        return {
            "vertex_text": self.get_current_vertex_text(),
            "edge_texts": self.get_current_edge_texts()
        }

    def get_current_vertex_text(self) -> str:
        """Return the current vertex dialogue text.

        Returns:
            str: Dialogue text for "self.current_vertex".
        """
        return self.graph.vertex_dict[self.current_vertex].text

    def proc_effect(self, effect: dict[str, str | int]) -> None:
        """Apply an effect to the game state.

        Args: 
            effect (dict[str, str | int]): Effect mapping to be processed.
        """
        match effect["type"]:
            case "modify_value":
                target_value = get_nested_attr(
                    self.game_state, effect["target"]
                )
                new_value = target_value + effect["delta"]
                set_nested_attr(self.game_state, effect["target"], new_value)
            case "modify_list":
                match effect["method"]:
                    case "append":
                        target_list = get_nested_attr(
                            self.game_state, effect["target"]
                        )
                        target_list.append(effect["value"])
                    case "remove":
                        target_list = get_nested_attr(
                            self.game_state, effect["target"]
                        )
                        target_list.remove(effect["value"])

    def select(self, edge_name: str) -> None:
        """Select an edge, apply effects, and move to the target vertex.

        Args:
            edge_name (str): Edge identifier to select.

        Raises:
            InvalidEdgeError: If the edge is not currently selectable.
        """
        if edge_name not in self.get_current_edges():
            raise InvalidEdgeError(
                f"Cannot select {edge_name} at vertex "
                f"{self.current_vertex} with the current game state. "
                f"{edge_name=}, "
                f"{self.current_vertex=}, "
                f"{self.graph=}, "
                f"{self.game_state=}"
            )
        edge = self.current_edges[edge_name]
        for effect in edge.effects:
            self.proc_effect(effect)
        self.enter_vertex(edge.to_vertex)


    