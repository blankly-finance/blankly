"""
    Allows the user to load the Keys in any Keys.json.
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import warnings

keys_path_cache = None

# This is currently unused
auth_cache = {}


def load_json(keys_file):
    try:
        f = open(keys_file)
        contents = json.load(f)
        f.close()
        return contents
    except FileNotFoundError:
        raise FileNotFoundError("Make sure a keys.json file is placed in the same folder as the project working "
                                "directory (or specified in the exchange constructor)!")


# def load_auth_coinbase_pro(keys_file, name):
#     exchange_type = "coinbase_pro"
#     name, portfolio = __load_auth(keys_file, name, exchange_type)
#
#     return [portfolio["API_KEY"], portfolio["API_SECRET"], portfolio["API_PASS"]], name
#
#
# def load_auth_binance(keys_file, name):
#     exchange_type = "binance"
#     name, portfolio = __load_auth(keys_file, name, exchange_type)
#
#     return [portfolio["API_KEY"], portfolio["API_SECRET"]], name


def load_auth(exchange_type, keys_file=None, name=None):
    global keys_path_cache

    if keys_file is None:
        if keys_path_cache is None:
            # Add a default for if info is passed in and nobody knows anything about paths
            keys_path_cache = './keys.json'
            keys_file = keys_path_cache
        else:
            # Default to the cached path if the passed variable is wrong
            keys_file = keys_path_cache
    else:
        # If its not non then there's no problem, just write it to the cache though
        keys_path_cache = keys_file

    auth_object = load_json(keys_file)
    exchange_keys = auth_object[exchange_type]
    if name is None:
        name, portfolio = __determine_first_key(exchange_keys)
    else:
        portfolio = exchange_keys[name]

    if exchange_type not in auth_cache:
        auth_cache[exchange_type] = {}
    return name, portfolio


def __determine_first_key(exchange_keys):
    first_key = list(exchange_keys.keys())[0]
    warning_string = "No portfolio name to load specified, defaulting to the first in the file: " \
                     "(" + first_key + "). This is fine if there is only one portfolio in use."
    warnings.warn(warning_string)
    # Read the first in the portfolio
    portfolio = exchange_keys[first_key]
    name = first_key
    return name, portfolio


def write_auth_cache(exchange, name, auth):
    """
    Write an authenticated object into the global authentication cache. This can be used by other pieces of code
    in the module to pull from exchanges at points they need the API

    Args:
        exchange (str): Exchange name ex: "coinbase_pro" or "binance"
        name (str): Portfolio name ex: "my cool portfolio"
        auth (obj): Authenticated object to store & recover.
    """
    global auth_cache
    if exchange not in auth_cache:
        auth_cache[exchange] = {}

    auth_cache[exchange][name] = auth


def read_auth_cache(exchange, name=None):
    """
    Pull an authenticated object on an exchange. This can be used for API calls anywhere in the code.
    """
    global auth_cache
    if exchange in auth_cache:
        if name is None:
            first_key = list(auth_cache[exchange])[0]
            return auth_cache[exchange][first_key]
        else:
            return auth_cache[exchange][name]
    else:
        raise KeyError("Request exchange invalid or does not exist")
