from dialogue_navigator.helper_functions import evaluate_text, get_operator
from dialogue_navigator.messages import MSG_INVALID_EDGE
from dialogue_navigator.state_accessor import (
    AttributeStateAccessor, StateAccessor
)
from dialogue_navigator.turn import Option, Turn
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

    def __init__(
        self,
        graph: Graph,
        *,
        game_state: object | None = None,
        accessor: StateAccessor | None = None
    ) -> None:
        """Initialize a navigator at the default starting vertex.

        Provide exactly one of game_state or accessor. Passing game_state
        wraps it in an AttributeStateAccessor, which resolves the dotted
        paths used by the graph's text, predicates, and effects as object
        attributes. Pass a custom accessor when game state is not stored
        as plain attributes.

        Args:
            graph (Graph): Dialogue graph to navigate.
            game_state (object | None): Mutable game state object whose
                attribute tree matches the graph's paths.
            accessor (StateAccessor | None): Custom state accessor.

        Raises:
            ValueError: If not exactly one of either game_state or accessor
                is provided.
        """
        if (game_state is None) == (accessor is None):
            raise ValueError(
                'Provide exactly one of "game_state" or "accessor".'
            )
        self.graph = graph
        self.accessor = (
            accessor 
            if accessor is not None 
            else AttributeStateAccessor(game_state)
        )
        validate(self.graph)
        self.enter_vertex(START_VERTEX)

    def __repr__(self) -> str:
        """Return a debug representation of this navigator.

        Returns:
            str: String representation of this navigator.
        """
        return (
            f"<Graph Navigator current_vertex={self.current_vertex!r} "
            f"options={len(self.current_edges)}>"
        )

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
                    current_value = self.accessor.get(predicate["path"])
                    predicate_value = predicate["value"]
                    if not(operator_function(current_value, predicate_value)):
                        is_valid_edge = False
                case PredicateType.CHECK_LIST:
                    operator_function = get_operator(predicate["op"])
                    current_list = self.accessor.get(predicate["path"])
                    predicate_value = predicate["value"]
                    if not(operator_function(predicate_value, current_list)):
                        is_valid_edge = False
        return is_valid_edge

    def get_current_turn(self) -> Turn:
        """Return the current turn for the game engine to present.

        Returns:
            Turn: Current vertex text, available player options, and whether
                the conversation is over, with all placeholders evaluated.
        """
        vertex = self.graph.vertex_dict[self.current_vertex]
        options = [
            Option(
                edge=edge_name,
                text=evaluate_text(edge.text, self.accessor)
            )
            for edge_name, edge in self.current_edges.items()
        ]
        return Turn(
            vertex=self.current_vertex,
            text=evaluate_text(vertex.text, self.accessor),
            options=options,
            is_over=not options
        )

    def proc_effect(self, effect: dict[str, str | int]) -> None:
        """Apply an effect to the game state.

        Args: 
            effect (dict[str, str | int]): Effect mapping to be processed.
        """
        match effect["type"]:
            case EffectType.MODIFY_VALUE:
                target_value = self.accessor.get(effect["target"])
                new_value = target_value + effect["delta"]
                self.accessor.set(effect["target"], new_value)
            case EffectType.MODIFY_LIST:
                match effect["method"]:
                    case ListMethod.APPEND:
                        target_list = self.accessor.get(effect["target"])
                        target_list.append(effect["value"])
                    case ListMethod.REMOVE:
                        target_list = self.accessor.get(effect["target"])
                        target_list.remove(effect["value"])

    def select(self, edge_name: str) -> None:
        """Select an edge, apply effects, and move to the target vertex.

        Args:
            edge_name (str): Edge identifier to select.

        Raises:
            InvalidEdgeError: If the edge is not currently selectable.
        """
        if edge_name not in self.current_edges:
            raise InvalidEdgeError(
                MSG_INVALID_EDGE.format(
                    edge_name=edge_name, current_vertex=self.current_vertex
                )
            )
        edge = self.current_edges[edge_name]
        for effect in edge.effects:
            self.proc_effect(effect)
        self.enter_vertex(edge.to_vertex)

    def respond_with(self, edge_name: str) -> Turn:
        """Syntatic sugar: select an edge and return the resulting turn.

        Args:
            edge_name (str): Edge identifier to select.

        Returns:
            Turn: The turn reached after selecting the edge.

        Raises:
            InvalidEdgeError: If the edge is not currently selectable.
        """
        self.select(edge_name)
        return self.get_current_turn()
    