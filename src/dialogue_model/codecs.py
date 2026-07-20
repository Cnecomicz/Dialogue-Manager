from re import match

from dialogue_model.constants import EffectType, ListMethod, PredicateType
from dialogue_model.messages import (
    MSG_UNKNOWN_EFFECT,
    MSG_UNKNOWN_EFFECT_SYNTAX,
    MSG_UNKNOWN_LIST_METHOD,
    MSG_UNKNOWN_PREDICATE,
    MSG_UNKNOWN_PREDICATE_SYNTAX
)

def convert_effect_to_text(effect: dict[str, str | int]) -> str:
    """Convert an effect dictionary into its single line text form.

    Args:
        effect (dict[str, str | int]): Effect mapping with a supported
            "type" key.

    Returns:
        str: Serialized effect expression.

    Raises:
        ValueError: If the effect type is not recognized.
    """
    match effect["type"]:
        case EffectType.MODIFY_VALUE:
            return (
                effect["target"] + " = "
                + effect["target"]
                + str(effect["delta"])
            )
        case EffectType.MODIFY_LIST:
            return (
                effect["target"] + "."
                + effect["method"] + "("
                + effect["value"] + ")"
            )
    raise ValueError(MSG_UNKNOWN_EFFECT.format(effect=effect))

def convert_predicate_to_text(predicate: dict[str, str | int]) -> str:
    """Convert a predicate dictionary into its single line text form.

    Args:
        predicate (dict[str, str | int]): Predicate mapping with a supported
            "type" key.

    Returns:
        str: Serialized predicate expression.

    Raises:
        ValueError: If the predicate type is not recognized.
    """
    match predicate["type"]:
        case PredicateType.CHECK_VALUE:
            return (
                predicate["path"] + " "
                + predicate["op"] + " "
                + str(predicate["value"])
            )
        case PredicateType.CHECK_LIST:
            return (
                str(predicate["value"]) + " "
                + predicate["op"] + " "
                + predicate["path"]
            )
    raise ValueError(MSG_UNKNOWN_PREDICATE.format(predicate=predicate))

def convert_text_to_effect(effect: str) -> dict[str, str | int]:
    """Parse text into an effect dictionary.

    Args:
        effect (str): Text expression representing an effect.

    Returns:
        dict[str, str | int]: Parsed effect mapping.

    Raises:
        ValueError: If the text does not match a supported effect syntax.

    Examples:
        "player.gold = player.gold+10" and "player.inventory.append(key)" are
        supported forms.
    """
    match_value = match(r"^(\w+(?:\.\w+)*) = \1(.+)$", effect)
    if match_value:
        target, delta = match_value.groups()
        try:
            delta = int(delta)
        except ValueError:
            pass
        return {
            "type": EffectType.MODIFY_VALUE.value, 
            "target": target, 
            "delta": delta
        }
    match_list = match(r"^(\w+(?:\.\w+)*)\.(\w+)\((.+)\)$", effect)
    if match_list:
        target, method, value = match_list.groups()
        if method not in set(ListMethod):
            raise ValueError(MSG_UNKNOWN_LIST_METHOD.format(effect=effect))
        return {
            "type": EffectType.MODIFY_LIST.value, 
            "target": target, 
            "method": method, 
            "value": value
        }
    raise ValueError(MSG_UNKNOWN_EFFECT_SYNTAX.format(effect=effect))

def convert_text_to_predicate(predicate: str) -> dict[str, str | int]:
    """Parse text into a predicate dictionary.

    Args:
        predicate (str): Text expression representing a predicate.

    Returns:
        dict[str, str | int]: Parsed predicate mapping.

    Raises:
        ValueError: If the text does not match a supported predicate syntax.

    Examples:
        "player.level >= 2" and "key in player.inventory" are supported forms.
    """
    match_value = match(
        r"^(\w+(?:\.\w+)*)\s*(==|!=|>=|<=|>|<)\s*(.+)$", predicate
    )
    if match_value:
        path, op, value = match_value.groups()
        try:
            value = int(value)
        except ValueError:
            pass
        return {
            "type": PredicateType.CHECK_VALUE.value, 
            "path": path, 
            "op": op, 
            "value": value
        }
    match_list = match(r"^(.+?)\s+(not in|in)\s+(\w+(?:\.\w+)*)$", predicate)
    if match_list:
        value, op, path = match_list.groups()
        stripped_value = value.strip()
        if stripped_value and stripped_value[0] in "<>=!":
            raise ValueError(
                MSG_UNKNOWN_PREDICATE_SYNTAX.format(predicate=predicate)
            )
        try:
            value = int(value)
        except ValueError:
            pass
        return {
            "type": PredicateType.CHECK_LIST.value, 
            "path": path, 
            "op": op, 
            "value": value
        }
    raise ValueError(MSG_UNKNOWN_PREDICATE_SYNTAX.format(predicate=predicate))