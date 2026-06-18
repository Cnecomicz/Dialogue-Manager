from operator import eq, ge, gt, le, lt, ne
from re import sub
from typing import Any, Callable

def evaluate_text(text: str, game_state: "GameState") -> str:
    """Evaluate placeholder expressions in text using the game state.

    Args:
        text (str): Text possibly containing placeholders like {player.gold}.
        game_state (GameState): Game state object for resolving values.

    Returns:
        str: Text with any placeholders replaced by evaluated values.
    """
    def replace_placeholder(match):
        attr_path = match.group(1)
        try:
            value = get_nested_attr(game_state, attr_path)
            return str(value)
        except AttributeError:
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

def get_nested_attr(obj: object, path: str) -> object:
    """Resolve a dotted attribute path from an object.

    Args:
        obj (object): Root object.
        path (str): Dotted path such as "player.equipment.weapon".

    Returns:
        object: Resolved nested attribute value.
    """
    for attr in path.split("."):
        obj = getattr(obj, attr)
    return obj

def set_nested_attr(obj: object, path: str, value: Any) -> None:
    """Set a dotted attribute path on an object.

    Args:
        obj (object): Root object.
        path (str): Dotted path such as "player.equipment.weapon".
        value (Any): Value to assign.
    """
    attrs = path.split(".")
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)
    setattr(obj, attrs[-1], value)


