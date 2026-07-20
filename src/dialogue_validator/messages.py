from dialogue_model.constants import MISSING_VERTEX, START_VERTEX

MSG_CLI_DESCRIPTION = (
    "Validate a dialogue graph yaml file for runtime validity."
)
MSG_CLI_VALID = "Graph is valid."
MSG_CLI_YAML_FILE_HELP = "Path to a .yaml or .yml dialogue graph file."
MSG_COMPONENT = "Component {index}: {component}"
MSG_COMPONENT_LINE = ". {component_string}"
MSG_DISCONNECTED_GRAPH = (
    "Graph is not connected. Found {count} connected components:"
)
MSG_ENDPOINT_NOT_FOUND = (
    'Edge "{edge_name}" {endpoint} endpoint references unknown vertex '
    '"{vertex_name}".'
)
MSG_INVALID_EFFECT = (
    'Effect in "{owner_name}" is invalid ({reason}): {effect}.'
)
MSG_INVALID_PREDICATE = (
    'Predicate in "{owner_name}" is invalid ({reason}): {predicate}.'
)
MSG_MALFORMED_PLACEHOLDER = (
    'Text in "{owner_name}" has malformed placeholder braces: "{text}".'
)
MSG_MISSING_EDGE_ENDPOINT = (
    'Edge "{edge_name}" has {endpoint} endpoint set to ' f'"{MISSING_VERTEX}".'
)
MSG_START_VERTEX_MISSING = (
    "Required start vertex " + f'"{START_VERTEX}" is missing.'
)
MSG_UNREACHABLE_VERTEX = (
    'Vertex "{vertex_name}" is unreachable from vertex ' f'"{START_VERTEX}".'
)
MSG_VALIDATION_HEADER = "Graph validation found {count} issue(s):"
MSG_VALIDATION_LINE = "- {error}"
REASON_MISSING_KEY = 'missing key "{key}"'
REASON_UNKNOWN_METHOD = "unknown method"
REASON_UNKNOWN_OPERATOR = "unknown operator"
REASON_UNKNOWN_TYPE = "unknown type"