from enum import StrEnum

EDGE_PREFIX = "edge_"
MISSING_VERTEX = "__MISSING__"
VERTEX_PREFIX = "vertex_"

START_VERTEX = f"{VERTEX_PREFIX}0"

class EffectType(StrEnum):
    """Enumerate the supported effect types."""

    MODIFY_LIST = "modify_list"
    MODIFY_VALUE = "modify_value"

class Endpoint(StrEnum):
    """Enumerate the edge endpoint labels."""

    FROM = "from"
    TO = "to"

class ListMethod(StrEnum):
    """Enumerate the supported list effect methods."""

    APPEND = "append"
    REMOVE = "remove"

class PredicateType(StrEnum):
    """Enumerate the supported predicate types."""

    CHECK_LIST = "check_list"
    CHECK_VALUE = "check_value"