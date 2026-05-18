from re import match

def convert_effect_to_text(effect: dict[str, str | int]) -> str:
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

def convert_predicate_to_text(predicate: dict[str, str | int]) -> str:
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

def convert_text_to_effect(effect: str) -> dict[str, str]:
    match_value = match(r"^(\w+(?:\.\w+)*) = \1(.+)$", effect)
    if match_value:
        target, delta = match_value.groups()
        try:
            delta = int(delta)
        except:
            delta = delta
        return {"type": "modify_value", "target": target, "delta": delta}
    match_list = match(r"^(\w+(?:\.\w+)*)\.(\w+)\((.+)\)$", effect)
    if match_list:
        target, method, value = match_list.groups()
        return {"type": "modify_list", "target": target, "method": method, "value": value}
