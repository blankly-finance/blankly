def is_sub_dict(dict1: dict, dict2: dict) -> bool:
    for key in dict1:
        if dict1[key] != dict2.get(key):
            return False

    return True


def validate_response(needed, resp):
    # verify resp is correct
    for key_type in needed:
        key = key_type[0]
        val_type = key_type[1]

        assert key in resp, f'{key} not in response'
        assert isinstance(resp[key], val_type), f'{key} has wrong value type'
