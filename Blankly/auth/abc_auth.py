"""
    Logic to provide consistency across exchanges
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

import abc
from Blankly.auth.utils import load_json

class auth_interface(abc.ABC):
    def __init__(self, keys_file, portfolio_name, exchange):
        """
        Create a currency interface
        Args:
            keys_file (str): filepath to keys.json
            portfolio_name (str): name of portfolio
        """
        assert keys_file
        assert portfolio_name
        assert exchange
        self.portfolio_name = portfolio_name
        self.exchange = exchange
        self.raw_cred = self.load_credentials(keys_file, portfolio_name, exchange)

    def load_credentials(self, keys_file, portfolio_name, exchange):
        """
        Load credentials from keys json file
        """
        auth_object = load_json(keys_file)
        exchange_keys = auth_object[exchange]
        credentials = exchange_keys[portfolio_name]

        return credentials

    @abc.abstractmethod
    def validate_credentials(self):
        """
        Validate that exchange specific credentials are present
        """
        pass
