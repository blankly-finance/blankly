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
import warnings

from blankly.exchanges.auth.auth_constructor import load_auth
from blankly.utils.exceptions import AuthError
from blankly.utils.utils import info_print


class ABCAuth(abc.ABC):
    def __init__(self, keys_file: str, portfolio_name: str, exchange: str):
        """
        Create a auth interface
        Args:
            keys_file (str): filepath to keys.json
            portfolio_name (str): name of portfolio
            exchange (str): name of exchange
        """
        # self.portfolio_name = portfolio_name
        self.exchange = exchange

        # Load from file
        self.portfolio_name, self.keys = load_auth(exchange, keys_file, portfolio_name)

    def validate_credentials(self, needed_keys: list):
        """
        Args:
            needed_keys (list): List of keys that the exchange needs in the format ['API_KEY', 'API_SECRET]

        Returns:
            A boolean that describes if the auth is good or bad (True if good).
        """

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
                if error_message == "":
                    error_message += "Error while loading authentication. Required keys for this are missing: \n"
                error_message += str(str(i) + " is needed, but not defined.\n")

        if len(keys_dict.keys()) > 0:
            info_print(f"Additional keys for Exchange: {self.exchange} Portfolio: {self.portfolio_name} will be"
                       f" ignored.")

        if error_message != "":
            raise AuthError(error_message)
