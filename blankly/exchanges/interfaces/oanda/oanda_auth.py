"""
    Coinbase authentication base class
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

from blankly.exchanges.auth.abc_auth import ABCAuth


class OandaAuth(ABCAuth):
    def __init__(self, keys_file, portfolio_name):
        super().__init__(keys_file, portfolio_name, 'oanda')
        needed_keys = ['PERSONAL_ACCESS_TOKEN', 'ACCOUNT_ID']
        self.validate_credentials(needed_keys)
