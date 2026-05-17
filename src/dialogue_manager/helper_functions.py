from operator import eq, ge, gt, le, lt, ne
from typing import Any, Callable

def get_operator(op: str) -> Callable[[object, object], bool]:
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
    for attr in path.split("."):
        obj = getattr(obj, attr)
    return obj

def set_nested_attr(obj: object, path: str, value: Any) -> None:
    attrs = path.split(".")
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)
    setattr(obj, attrs[-1], value)


