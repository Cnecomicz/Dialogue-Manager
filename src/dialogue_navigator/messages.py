from dialogue_model.constants import START_VERTEX

MSG_COMPONENT = "Component {index}: {component}"
MSG_COMPONENT_LINE = ". {component_string}"
MSG_DISCONNECTED_GRAPH = (
    "Graph is not connected. Found {count} connected components:"
)
MSG_ENDPOINT_NOT_FOUND = (
    'Edge "{edge_name}" {endpoint} endpoint references unknown vertex '
    '"{vertex_name}".'
)
MSG_INVALID_EDGE = (
    "Cannot select {edge_name} at vertex {current_vertex} with the "
    "current game state."
)
MSG_MISSING_EDGE_ENDPOINT = (
    'Edge "{edge_name}" has {endpoint} endpoint set to "{missing_vertex}".'
)
MSG_START_VERTEX_MISSING = (
    "Required start vertex " + f'"{START_VERTEX}" is missing.'
)
MSG_UNREACHABLE_VERTEX = (
    'Vertex "{vertex_name}" is unreachable from vertex ' + f'"{START_VERTEX}".'
)
MSG_VALIDATION_ERROR_LINE = "- {error}"
MSG_VALIDATION_FAILED_HEADER = "Graph failed runtime validation:"