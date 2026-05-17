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

def convert_filter_to_text(condition: dict[str, str | int]) -> str:
    match condition["type"]:
        case "check_value":
            return (
                condition["path"] + " "
                + condition["op"] + " "
                + str(condition["value"])
            )
        case "check_list":
            return (
                str(condition["value"]) + " "
                + condition["op"] + " "
                + condition["path"]
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
