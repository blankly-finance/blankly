"""
    Comparison utilities for tests
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
