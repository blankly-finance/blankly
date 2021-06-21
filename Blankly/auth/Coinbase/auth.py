"""
    Coinbase authentication base class
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


from Blankly.auth.abc_auth import AuthInterface
import warnings


class CoinbaseAuth(AuthInterface):
    def __init__(self, keys_file, portfolio_name):
        super().__init__(keys_file, portfolio_name, 'coinbase_pro')
        needed_keys = ['API_KEY', 'API_SECRET', 'API_PASS']

        self.validate_credentials(needed_keys)

    def validate_credentials(self, needed_keys: list):
        """
        Validate that exchange specific credentials are present
        """
        super().validate_credentials(needed_keys)
            print(f"One of 'API_KEY' or 'API_SECRET' or 'API_PASS' not defined for "
                  f"Exchange: {self.exchange} Portfolio: {self.portfolio_name}")
            raise KeyError(e)
