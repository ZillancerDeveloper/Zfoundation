from importlib import import_module


def import_callable(path_or_callable):
    if hasattr(path_or_callable, "__call__"):
        return path_or_callable
    else:
        assert isinstance(path_or_callable, str)
        package, attr = path_or_callable.rsplit(".", 1)
        return getattr(import_module(package), attr)


def mergedicts(dict1, dict2):
    d = dict1["menu_action"]
    for k in dict2["menu_action"]:
        if k not in dict1["menu_action"]:
            d.append(k)

    return_dict = {
        "menu": dict1["menu"],
        "menu_action": d,
    }

    return return_dict
