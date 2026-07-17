from dialogue_model.constants import (
    EFFECT_REQUIRED_KEYS,
    EffectType,
    Endpoint,
    ListMethod,
    MISSING_VERTEX,
    PREDICATE_REQUIRED_KEYS,
    PredicateType,
    START_VERTEX
)
from dialogue_model.graph import Graph
from dialogue_validator.messages import (
    MSG_COMPONENT,
    MSG_COMPONENT_LINE,
    MSG_DISCONNECTED_GRAPH,
    MSG_ENDPOINT_NOT_FOUND,
    MSG_INVALID_EFFECT,
    MSG_INVALID_PREDICATE,
    MSG_MALFORMED_PLACEHOLDER,
    MSG_MISSING_EDGE_ENDPOINT,
    MSG_START_VERTEX_MISSING,
    MSG_UNREACHABLE_VERTEX,
    MSG_VALIDATION_HEADER,
    MSG_VALIDATION_LINE,
    REASON_MISSING_KEY,
    REASON_UNKNOWN_METHOD,
    REASON_UNKNOWN_TYPE
)

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
            MSG_VALIDATION_HEADER,
            *[
                MSG_VALIDATION_LINE.format(error=error) 
                for error in errors
            ]
        ]
        super().__init__("\n".join(message_lines))

class DisconnectedGraphError(Exception):
    """Raised when graph has multiple connected components."""

    def __init__(self, components: list[list[str]]) -> None:
        """Initialize the error with the connected components.

        Args:
            components (list[list[str]]): List of vertex lists, each
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

class InvalidEffectError(Exception):
    """Raised when a vertex or edge effect is not well-formed."""

    def __init__(
        self, owner_name: str, effect: dict[str, str | int], reason: str
    ) -> None:
        """Initialize the error with the offending effect and reason.

        Args:
            owner_name (str): Identifier of the vertex or edge owning the
                effect.
            effect (dict[str, str | int]): The malformed effect mapping.
            reason (str): Explanation of why the effect is invalid.
        """
        self.owner_name = owner_name
        self.effect = effect
        self.reason = reason
        super().__init__(
            MSG_INVALID_EFFECT.format(
                owner_name=owner_name, reason=reason, effect=effect
            )
        )

class InvalidPredicateError(Exception):
    """Raised when an edge predicate is not well-formed."""

    def __init__(
        self, owner_name: str, predicate: dict[str, str | int], reason: str
    ) -> None:
        """Initialize the error with the offending predicate and reason.

        Args:
            owner_name (str): Identifier of the edge owning the predicate.
            predicate (dict[str, str | int]): The malformed predicate mapping.
            reason (str): Explanation of why the predicate is invalid.
        """
        self.owner_name = owner_name
        self.predicate = predicate
        self.reason = reason
        super().__init__(
            MSG_INVALID_PREDICATE.format(
                owner_name=owner_name, reason=reason, predicate=predicate
            )
        )

class MalformedPlaceholderError(Exception):
    """Raised when text has unbalanced or malformed placeholder braces."""

    def __init__(self, owner_name: str, text: str) -> None:
        """Initialize the error with the offending owner and text.

        Args:
            owner_name (str): Identifier of the vertex or edge owning the text.
            text (str): The text with malformed placeholder braces.
        """
        self.owner_name = owner_name
        self.text = text
        super().__init__(
            MSG_MALFORMED_PLACEHOLDER.format(owner_name=owner_name, text=text)
        )

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
    for vertex_name, vertex in graph.vertex_dict.items():
        for effect in vertex.effects:
            reason = get_effect_error_reason(effect)
            if reason is not None:
                errors.append(
                    InvalidEffectError(vertex_name, effect, reason)
                )
        if has_malformed_braces(vertex.text):
            errors.append(MalformedPlaceholderError(vertex_name, vertex.text))
    for edge_name, edge in graph.edge_dict.items():
        for effect in edge.effects:
            reason = get_effect_error_reason(effect)
            if reason is not None:
                errors.append(InvalidEffectError(edge_name, effect, reason))
        for predicate in edge.predicates:
            reason = get_predicate_error_reason(predicate)
            if reason is not None:
                errors.append(
                    InvalidPredicateError(edge_name, predicate, reason)
                )
        if has_malformed_braces(edge.text):
            errors.append(MalformedPlaceholderError(edge_name, edge.text))
    return errors

def get_effect_error_reason(effect: dict[str, str | int]) -> str | None:
    """Return the reason an effect is invalid, or None if valid.

    Args:
        effect (dict[str, str | int]): Effect mapping to inspect.

    Returns:
        str | None: A short reason string, or None when valid.
    """
    effect_type = effect.get("type")
    if effect_type not in set(EffectType):
        return REASON_UNKNOWN_TYPE
    for key in EFFECT_REQUIRED_KEYS[EffectType(effect_type)]:
        if key not in effect:
            return REASON_MISSING_KEY.format(key=key)
    if (
        effect_type == EffectType.MODIFY_LIST 
        and effect["method"] not in set(ListMethod)
    ):
        return REASON_UNKNOWN_METHOD
    return None

def get_predicate_error_reason(predicate: dict[str, str | int]) -> str | None:
    """Return the reason a predicate is invalid, or None if valid.

    Args:
        predicate (dict[str, str | int]): Predicate mapping to inspect.

    Returns:
        str | None: A short reason string, or None when valid.
    """
    predicate_type = predicate.get("type")
    if predicate_type not in set(PredicateType):
        return REASON_UNKNOWN_TYPE
    for key in PREDICATE_REQUIRED_KEYS[PredicateType(predicate_type)]:
        if key not in predicate:
            return REASON_MISSING_KEY.format(key=key)
    return None

def has_malformed_braces(text: str) -> bool:
    """Return whether text contains malformed placeholder braces.

    Placeholders must form nonnested nonempty { } pairs.

    Args:
        text (str): Text to inspect for placeholder braces.

    Returns:
        bool: True when a brace is unbalanced, nested, or empty.
    """
    is_open = False
    content_length = 0
    for character in text:
        if character == "{":
            if is_open:
                return True
            is_open = True
            content_length = 0
        elif character == "}":
            if not is_open or content_length == 0:
                return True
            is_open = False
        elif is_open:
            content_length += 1
    return is_open

def validate(graph: Graph) -> None:
    """Validate a graph, raising an aggregate error when it is invalid.

    Args:
        graph (Graph): Dialogue graph to validate.

    Raises:
        AggregatedValidationErrors: If the graph has any validation errors.
    """
    errors = collect_validation_errors(graph)
    if errors:
        raise AggregatedValidationErrors(errors)