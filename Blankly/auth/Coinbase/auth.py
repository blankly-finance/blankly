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
        self.API_KEY = None
        self.API_SECRET = None
        self.API_PASS = None

        self.validate_credentials()

    def validate_credentials(self):
        """
        Validate that exchange specific credentials are present
        """
        try:
            self.API_KEY = self.raw_cred.pop('API_KEY')
            self.API_SECRET = self.raw_cred.pop('API_SECRET')
            self.API_PASS = self.raw_cred.pop('API_PASS')
        except KeyError as e:
            print(f"One of 'API_KEY' or 'API_SECRET' or 'API_PASS' not defined for "
                  f"Exchange: {self.exchange} Portfolio: {self.portfolio_name}")
            raise KeyError(e)

        if len(self.raw_cred) > 0:
            warnings.warn(f"Additional keys for Exchange: {self.exchange} Portfolio: {self.portfolio_name} will be"
                          f" ignored.")



