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

import json, warnings

def load_json(keys_file):
    try:
        f = open(keys_file)
        return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError("Make sure a Keys.json file is placed in the same folder as the project working "
                                "directory!")


def load_auth_coinbase_pro(keys_file, name):
    auth_object = load_json(keys_file)
    exchange_keys = auth_object["coinbase_pro"]
    if name is None:
        first_key = list(exchange_keys.keys())[0]
        warning_string = "No portfolio name to load specified, defaulting to the first in the file: " \
                         "(" + first_key + "). This is fine if there is only one portfolio in use."
        warnings.warn(warning_string)
        # Read the first in the portfolio
        portfolio = exchange_keys[first_key]
        name = first_key
    else:
        portfolio = exchange_keys[name]

    return [portfolio["API_KEY"], portfolio["API_SECRET"], portfolio["API_PASS"]], name


def load_auth_binance(keys_file):
    auth_object = load_json(keys_file)
    exchange_keys = auth_object["binance"]
    return [exchange_keys["API_KEY"], exchange_keys["API_SECRET"]]
