from operator import eq, ge, gt, le, lt, ne
from re import sub
from typing import Callable

from dialogue_navigator.state_accessor import GameStatePathError, StateAccessor

def evaluate_text(text: str, accessor: StateAccessor) -> str:
    """Evaluate placeholder expressions in text using game state values.

    Args:
        text (str): Text possibly containing placeholders like {player.gold}.
        accessor (StateAccessor): Accessor for resolving game state values.

    Returns:
        str: Text with any resolvable placeholders replaced by their values.
            Unresolvable placeholders are left unchanged.
    """
    def replace_placeholder(match):
        attr_path = match.group(1)
        try:
            value = accessor.get(attr_path)
            return str(value)
        except GameStatePathError:
            return match.group(0)
    return sub(r"\{([^}]+)\}", replace_placeholder, text)

def get_operator(op: str) -> Callable[[object, object], bool]:
    """Return the comparison function for a predicate operator string.

    Args:
        op (str): Operator token such as "==" or "in".

    Returns:
        Callable[[object, object], bool]: Callable implementing the operator.
    """
    operators = {
        "==": eq, 
        ">=": ge, 
        ">": gt, 
        "in": lambda a, b: a in b, 
        "<=": le, 
        "<": lt, 
        "!=": ne,
        "not in": lambda a, b: a not in b,
    }
    return operators[op]