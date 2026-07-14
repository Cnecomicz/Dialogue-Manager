from dialogue_navigator.helper_functions import (
    evaluate_text, get_operator, get_nested_attr, set_nested_attr
)
from dialogue_navigator.messages import (
    MSG_COMPONENT,
    MSG_COMPONENT_LINE,
    MSG_DISCONNECTED_GRAPH,
    MSG_ENDPOINT_NOT_FOUND,
    MSG_INVALID_EDGE,
    MSG_MISSING_EDGE_ENDPOINT,
    MSG_START_VERTEX_MISSING,
    MSG_UNREACHABLE_VERTEX,
    MSG_VALIDATION_ERROR_LINE,
    MSG_VALIDATION_FAILED_HEADER
)
from dialogue_model.constants import (
    EffectType,
    Endpoint,
    ListMethod,
    MISSING_VERTEX,
    PredicateType,
    START_VERTEX
)
from dialogue_model.edge import Edge
from dialogue_model.graph import Graph

class AggregatedValidationErrors(Exception):
    """Aggregate graph validation errors."""

    def __init__(self, errors: list[Exception]) -> None:
        """Initialize the aggregate error from individual validation errors.

        Args:
            errors (list[Exception]): Individual validation errors gathered
                for the graph.
        """
        self.errors = errors
        message_lines = [
            MSG_VALIDATION_FAILED_HEADER,
            *[
                MSG_VALIDATION_ERROR_LINE.format(error=error) 
                for error in errors
            ]
        ]
        super().__init__("\n".join(message_lines))

class DisconnectedGraphError(Exception):
    """Raised when graph has multiple connected components."""

    def __init__(self, components: list[list[str]]) -> None:
        """Initialize the error with the connected components.

        Args:
            components (list[str[str]]): List of vertex lists, each
                representing a connected component.
        """
        self.components = components
        component_strings = [
            MSG_COMPONENT.format(index=i+1, component=component)
            for i, component in enumerate(components)
        ]
        message = (
            MSG_DISCONNECTED_GRAPH.format(count=len(components)) + "\n"
            + "\n".join(
                MSG_COMPONENT_LINE.format(component_string=string)
                for string in component_strings
            )
        )
        super().__init__(message)

class EndpointNotFoundError(Exception):
    """Raised when an edge endpoint references an unknown vertex."""

    def __init__(
        self, edge_name: str, endpoint: str, vertex_name: str
    ) -> None:
        """Initialize the error with the offending edge, endpoint, and vertex.

        Args:
            edge_name (str): Identifier of the edge with the bad endpoint.
            endpoint (str): Endpoint label, either "from" or "to".
            vertex_name (str): Unknown vertex identifier that was referenced.
        """
        self.edge_name = edge_name
        self.endpoint = endpoint
        self.vertex_name = vertex_name
        super().__init__(
            MSG_ENDPOINT_NOT_FOUND.format(
                edge_name=edge_name, endpoint=endpoint, vertex_name=vertex_name
            )
        )

class InvalidEdgeError(Exception):
    """Raised when a selected edge is not valid for the current state."""

    pass

class MissingEdgeEndpointError(Exception):
    """Raised when an edge endpoint is set to "__MISSING__"."""

    def __init__(self, edge_name: str, endpoint: str) -> None:
        """Initialize the error with the offending edge and endpoint.

        Args:
            edge_name (str): Identifier of the edge with the bad endpoint.
            endpoint (str): Endpoint label, either "from" or "to".
        """
        self.edge_name = edge_name
        self.endpoint = endpoint
        super().__init__(
            MSG_MISSING_EDGE_ENDPOINT.format(
                edge_name=edge_name, 
                endpoint=endpoint, 
                missing_vertex=MISSING_VERTEX
            )
        )


class StartVertexMissingError(Exception):
    """Raised when the graph has no starting vertex (vertex_0)."""

    pass

class UnreachableVertexError(Exception):
    """Raised when a vertex is unreachable from the starting one (vertex_0)."""

    def __init__(self, vertex_name: str) -> None:
        """Initialize the error with the unreachable vertex name.

        Args:
            vertex_name (str): Identifier of the unreachable vertex.
        """
        self.vertex_name = vertex_name
        super().__init__(
            MSG_UNREACHABLE_VERTEX.format(vertex_name=vertex_name)
        )

def collect_validation_errors(graph: Graph) -> list[Exception]:
    """Collect all runtime validation errors.

    Args:
        graph (Graph): Dialogue graph to validate.

    Returns:
        list[Exception]: All validation errors found, or an empty list
            when the graph is valid.
    """
    errors = []
    vertex_names = set(graph.vertex_dict.keys())
    if START_VERTEX not in vertex_names:
        errors.append(
            StartVertexMissingError(
                MSG_START_VERTEX_MISSING.format(start_vertex=START_VERTEX)
            )
        )
    for edge_name, edge in graph.edge_dict.items():
        endpoints = [
            (Endpoint.FROM, edge.from_vertex), (Endpoint.TO, edge.to_vertex)
        ]
        for endpoint, vertex_name in endpoints:
            if vertex_name == MISSING_VERTEX:
                errors.append(
                    MissingEdgeEndpointError(edge_name, endpoint)
                )
            elif vertex_name not in vertex_names:
                errors.append(
                    EndpointNotFoundError(edge_name, endpoint, vertex_name)
                )
    if START_VERTEX in vertex_names:
        already_reachable_vertices = {START_VERTEX}
        frontier_of_traversed_vertices = [START_VERTEX]
        while frontier_of_traversed_vertices:
            current_vertex = frontier_of_traversed_vertices.pop()
            for edge in graph.edge_dict.values():
                source = edge.from_vertex
                target = edge.to_vertex
                if (
                    source == current_vertex
                    and source in vertex_names
                    and target in vertex_names
                    and source != MISSING_VERTEX
                    and target != MISSING_VERTEX
                    and target not in already_reachable_vertices
                ):
                    already_reachable_vertices.add(target)
                    frontier_of_traversed_vertices.append(target)
        for vertex_name in sorted(
            vertex_names - already_reachable_vertices
        ):
            errors.append(UnreachableVertexError(vertex_name))
    visited_vertices = set()
    connected_components = []
    for vertex_name in sorted(vertex_names):
        if vertex_name not in visited_vertices:
            component = set()
            frontier = [vertex_name]
            while frontier:
                current_vertex = frontier.pop()
                if current_vertex in visited_vertices:
                    continue
                visited_vertices.add(current_vertex)
                component.add(current_vertex)
                for edge in graph.edge_dict.values():
                    if (
                        edge.from_vertex in vertex_names
                        and edge.to_vertex in vertex_names
                    ):
                        if (
                            edge.from_vertex == current_vertex
                            and edge.to_vertex not in visited_vertices
                        ):
                            frontier.append(edge.to_vertex)
                        elif (
                            edge.to_vertex == current_vertex
                            and edge.from_vertex not in visited_vertices
                        ):
                            frontier.append(edge.from_vertex)
            if component:
                connected_components.append(sorted(component))
        if len(connected_components) > 1:
            errors.append(DisconnectedGraphError(connected_components))
    return errors

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
        self.validate_graph()
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
            bool: "True" when every predicate is satisified.
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
        return {self.current_vertex:  evaluated_text}

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

    def validate_graph(self) -> None:
        """Raise errors if graph is invalid.

        Raises:
            AggregatedValidationErrors: If the graph has any validation errors.
        """
        errors = collect_validation_errors(self.graph)
        if errors:
            raise AggregatedValidationErrors(errors)


    