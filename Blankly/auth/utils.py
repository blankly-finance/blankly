"""
    Utils for constructing authentication
    Copyright (C) 2021  Emerson Dove, Arun Annamalai

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


def load_json(keys_file):
    try:
        f = open(keys_file)
        contents = json.load(f)
        f.close()
        return contents
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
