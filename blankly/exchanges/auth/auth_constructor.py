"""
    Inherited authentication object
    Copyright (C) 2021  Arun Annamalai, Emerson Dove

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

import abc
import json

from blankly.exchanges.auth.utils import load_auth
from blankly.utils.exceptions import AuthError
from blankly.utils.utils import info_print


class AuthConstructor(abc.ABC):
    def __init__(self, keys_file: str, portfolio_name: str, exchange: str, needed_keys: list):
        """
        Create an auth interface
        Args:
            keys_file (str): filepath to keys.json
            portfolio_name (str): name of portfolio
            exchange (str): name of exchange
        """
        # self.portfolio_name = portfolio_name
        self.exchange = exchange

        # Load from file
        self.portfolio_name, self.keys = load_auth(exchange, keys_file, portfolio_name)

        # Create an error message template to throw if needed
        error_message = ""

        # Make a copy of the keys dict & list to avoid modifying passed variables
        keys_dict = {**self.keys}
        needed_keys = list.copy(needed_keys)
        for i in needed_keys:
            if i in keys_dict.keys():
                keys_dict.pop(i)
            else:
                # Append a description header if not present
                example_str = json.dumps({'portfolio': {'API_KEY': '********************',
                                                        'API_SECRET': '********************',
                                                        f'{i}': False}}, indent=2)
                if error_message == "":
                    error_message += f"Error while loading authentication. Required keys for this are missing: \n" \
                                     f"Please add the \"{i}\" key to the keys.json file. For example: \n" \
                                     f"{example_str}"

                if i != "sandbox":
                    raise AuthError(error_message)
                else:
                    info_print(f"Please add the sandbox keys to your keys.json file. The use_sandbox setting will be "
                               f"removed in the next update: \n"
                               f"{example_str}")

        if len(keys_dict.keys()) > 0:
            info_print(f"Additional keys for Exchange: {self.exchange} Portfolio: {self.portfolio_name} will be"
                       f" ignored.")
