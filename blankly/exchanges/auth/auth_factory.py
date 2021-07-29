"""
    Switch system to find correct authentication method
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

from blankly.exchanges.interfaces.alpaca.alpaca_auth import AlpacaAuth
from blankly.exchanges.interfaces.binance.binance_auth import BinanceAuth
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_auth import CoinbaseProAuth
from blankly.exchanges.interfaces.oanda.oanda_auth import OandaAuth


class AuthFactory:
    @staticmethod
    def create_auth(keys_file, exchange_name, portfolio_name):
        if exchange_name == 'alpaca':
            return AlpacaAuth(keys_file, portfolio_name)
        elif exchange_name == 'binance':
            return BinanceAuth(keys_file, portfolio_name)
        elif exchange_name == 'coinbase_pro':
            return CoinbaseProAuth(keys_file, portfolio_name)
        elif exchange_name == 'oanda':
            return OandaAuth(keys_file, portfolio_name)
        elif exchange_name == 'paper_trade':
            return None
        else:
            raise KeyError("Exchange not supported")
