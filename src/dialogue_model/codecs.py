from re import match

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
        case "modify_value":
            return (
                effect["target"] + " = "
                + effect["target"]
                + str(effect["delta"])
            )
        case "modify_list":
            return (
                effect["target"] + "."
                + effect["method"] + "("
                + effect["value"] + ")"
            )
    raise ValueError(f"Unknown effect: {effect}")

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
        case "check_value":
            return (
                predicate["path"] + " "
                + predicate["op"] + " "
                + str(predicate["value"])
            )
        case "check_list":
            return (
                str(predicate["value"]) + " "
                + predicate["op"] + " "
                + predicate["path"]
            )
    raise ValueError(f"Unknown predicate: {predicate}")

def convert_text_to_effect(effect: str) -> dict[str, str | int]:
    """Parse text into an effect dictionary.

    Args:
        effect (str): Text expression representing an effect.

    Returns:
        dict[str, str | int] Parsed effect mapping.

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
            delta = delta
        return {"type": "modify_value", "target": target, "delta": delta}
    match_list = match(r"^(\w+(?:\.\w+)*)\.(\w+)\((.+)\)$", effect)
    if match_list:
        target, method, value = match_list.groups()
        return {
            "type": "modify_list", 
            "target": target, 
            "method": method, 
            "value": value
        }
    raise ValueError(f"Unknown effect syntax: {effect}")

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
            value = value
        return {"type": "check_value", "path": path, "op": op, "value": value}
    match_list = match(r"^(.+?)\s+(not in|in)\s+(\w+(?:\.\w+)*)$", predicate)
    if match_list:
        value, op, path = match_list.groups()
        try:
            value = int(value)
        except ValueError:
            value = value
        return {"type": "check_list", "path": path, "op": op, "value": value}
    raise ValueError(f"Unknown predicate syntax: {predicate}")