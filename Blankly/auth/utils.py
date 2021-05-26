import json
import warnings

def load_json(keys_file):
    try:
        f = open(keys_file)
        return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("Make sure a Keys.json file is placed in the same folder as the project working "
                                "directory!")

def default_first_portfolio(keys_file, exchange_name):
    auth_object = load_json(keys_file)
    exchange_keys = auth_object[exchange_name]
    first_key = list(exchange_keys.keys())[0]
    warning_string = "No portfolio name to load specified, defaulting to the first in the file: " \
                     "(" + first_key + "). This is fine if there is only one portfolio in use."
    warnings.warn(warning_string)
    # Read the first in the portfolio
    portfolio = exchange_keys[first_key]
    name = first_key
    return name, portfolio