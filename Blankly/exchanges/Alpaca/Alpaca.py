"""
    Alpaca exchange definitions and setup
    Copyright (C) 2021  Emerson Dove, Arun Annamalai, Brandon Fan

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

from Blankly.exchanges.exchange import Exchange
from Blankly.auth.auth_factory import AuthFactory
from Blankly.auth.utils import default_first_portfolio
from Blankly.interface.currency_factory import InterfaceFactory

class Alpaca(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", preferences_path=None):
        if not portfolio_name:
            portfolio_name = default_first_portfolio(keys_path, 'alpaca')
        Exchange.__init__(self, 'alpaca', portfolio_name, keys_path, preferences_path)


