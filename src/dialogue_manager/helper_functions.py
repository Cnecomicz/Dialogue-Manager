from operator import eq, ge, gt, le, lt, ne
from typing import Any

def get_operator(op: str):
    match op:
        case ">":
            return gt
        case ">=":
            return ge
        case "<":
            return lt
        case "<=":
            return le
        case "==":
            return eq
        case "!=":
            return ne

def get_nested_attr(obj: object, path: str):
    for attr in path.split("."):
        obj = getattr(obj, attr)
    return obj

def set_nested_attr(obj: object, path: str, value: Any):
    attrs = path.split(".")
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)
    setattr(obj, attrs[-1], value)


