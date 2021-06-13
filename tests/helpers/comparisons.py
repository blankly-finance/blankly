def is_sub_dict(dict1: dict, dict2: dict) -> bool:
    for key in dict1:
        if dict1[key] != dict2.get(key):
            return False

    return True
