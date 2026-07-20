from enum import StrEnum

EDGE_PREFIX = "edge_"
MISSING_VERTEX = "__MISSING__"
VERTEX_PREFIX = "vertex_"

START_VERTEX = f"{VERTEX_PREFIX}0"

class EffectType(StrEnum):
    """Enumerate the supported effect types."""

    MODIFY_LIST = "modify_list"
    MODIFY_VALUE = "modify_value"

EFFECT_REQUIRED_KEYS = {
    EffectType.MODIFY_LIST: ("target", "method", "value"),
    EffectType.MODIFY_VALUE: ("target", "delta")
}

class Endpoint(StrEnum):
    """Enumerate the edge endpoint labels."""

    FROM = "from"
    TO = "to"

class ListMethod(StrEnum):
    """Enumerate the supported list effect methods."""

    APPEND = "append"
    REMOVE = "remove"

class ListOperator(StrEnum):
    """Enumerate the supported list membership operators."""

    IN = "in"
    NOT_IN = "not in"

class PredicateType(StrEnum):
    """Enumerate the supported predicate types."""

    CHECK_LIST = "check_list"
    CHECK_VALUE = "check_value"

class ValueOperator(StrEnum):
    """Enumerate the supported value comparison operators."""

    EQUAL = "=="
    GREATER = ">"
    GREATER_OR_EQUAL = ">="
    LESS = "<"
    LESS_OR_EQUAL = "<="
    NOT_EQUAL = "!="

PREDICATE_ALLOWED_OPERATORS = {
    PredicateType.CHECK_LIST: set(ListOperator),
    PredicateType.CHECK_VALUE: set(ValueOperator)
}
PREDICATE_REQUIRED_KEYS = {
    PredicateType.CHECK_LIST: ("path", "op", "value"),
    PredicateType.CHECK_VALUE: ("path", "op", "value")
}