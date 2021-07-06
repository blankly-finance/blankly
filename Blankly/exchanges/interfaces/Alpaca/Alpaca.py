"""
    Alpaca exchange definitions and setup
    Copyright (C) 2021 Arun Annamalai, Emerson Dove, Brandon Fan

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
import alpaca_trade_api


class Alpaca(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, 'alpaca', portfolio_name, keys_path, settings_path)

    def get_exchange_state(self):
        return self.Interface.get_fees()

    def get_currency_state(self, currency):
        return self.Interface.get_account(currency)

    def get_direct_calls(self) -> alpaca_trade_api.REST:
        return self.calls
