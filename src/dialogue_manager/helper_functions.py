from operator import eq, ge, gt, le, lt, ne

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