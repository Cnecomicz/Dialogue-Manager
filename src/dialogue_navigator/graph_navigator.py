from dialogue_navigator.helper_functions import (
    evaluate_text, get_operator, get_nested_attr, set_nested_attr
)
from dialogue_navigator.messages import MSG_INVALID_EDGE
from dialogue_model.constants import (
    EffectType, ListMethod, PredicateType, START_VERTEX
)
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph
from dialogue_validator.graph_validator import validate

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
        validate(self.graph)
        self.enter_vertex(START_VERTEX)

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
            bool: "True" when every predicate is satisfied.
        """
        edge = self.graph.edge_dict[edge_name]
        is_valid_edge = True
        for predicate in edge.predicates:
            match predicate["type"]:
                case PredicateType.CHECK_VALUE:
                    operator_function = get_operator(predicate["op"])
                    current_value = get_nested_attr(
                        self.game_state, predicate["path"]
                    )
                    predicate_value = predicate["value"]
                    if not(operator_function(current_value, predicate_value)):
                        is_valid_edge = False
                case PredicateType.CHECK_LIST:
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
        """Return current selectable edge text keyed by edge_name, with 
        placeholders evaluated.

        Returns:
            dict[str, str]: Mapping of edge_name to edge dialogue text.
        """
        return {
            edge_name: evaluate_text(edge.text, self.game_state)
            for edge_name, edge in self.current_edges.items()
        }

    def get_current_turn(self) -> dict[str, dict[str, str]]:
        """Return current turn text payload for game UI handshakes.

        Returns:
            dict[str, dict[str, str]]: Mapping containing current
            vertex dialogue text and available edge text options.
        """
        return {
            "vertex_text": self.get_current_vertex_text(),
            "edge_texts": self.get_current_edge_texts()
        }

    def get_current_vertex_text(self) -> dict[str, str]:
        """Return the current vertex dialogue text keyed by vertex_name, with
        placeholders evaluated.

        Returns:
            dict[str, str]: Mapping of "self.current_vertex" to vertex dialogue
            text.
        """
        vertex_text = self.graph.vertex_dict[self.current_vertex].text
        evaluated_text = evaluate_text(vertex_text, self.game_state)
        return {self.current_vertex: evaluated_text}

    def proc_effect(self, effect: dict[str, str | int]) -> None:
        """Apply an effect to the game state.

        Args: 
            effect (dict[str, str | int]): Effect mapping to be processed.
        """
        match effect["type"]:
            case EffectType.MODIFY_VALUE:
                target_value = get_nested_attr(
                    self.game_state, effect["target"]
                )
                new_value = target_value + effect["delta"]
                set_nested_attr(self.game_state, effect["target"], new_value)
            case EffectType.MODIFY_LIST:
                match effect["method"]:
                    case ListMethod.APPEND:
                        target_list = get_nested_attr(
                            self.game_state, effect["target"]
                        )
                        target_list.append(effect["value"])
                    case ListMethod.REMOVE:
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
                MSG_INVALID_EDGE.format(
                    edge_name=edge_name, current_vertex=self.current_vertex
                )
            )
        edge = self.current_edges[edge_name]
        for effect in edge.effects:
            self.proc_effect(effect)
        self.enter_vertex(edge.to_vertex)


    