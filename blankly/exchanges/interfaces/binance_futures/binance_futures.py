"""
    Binance Futures Exchange object.
    Copyright (C) 2021 Matias Kotlik

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

from binance.futures import Futures

from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.binance_futures.binance_futures_interface import BinanceFuturesInterface
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface


def get_binance_url(preferences: dict) -> str:
    margin_type = preferences['settings']['binance']['futures']['margin_type']
    if margin_type == 'COIN-M':
        raise NotImplementedError(
            'COIN-M Futures are not implemented at this time.')
        # url_prefix = 'dapi'
    elif margin_type == 'USDT-M':
        url_prefix = 'fapi'
    else:
        raise ValueError(
            f"Invalid margin_type for binance_futures: {margin_type}. Must be either 'USDT-M' or 'COIN-M'."
        )

    if preferences['settings']['use_sandbox']:
        return 'https://testnet.binancefuture.com'
    else:
        return f'https://{url_prefix}.binance.com'


class BinanceFutures(FuturesExchange):

    def __init__(self,
                 portfolio_name=None,
                 keys_path="keys.json",
                 preferences_path=None):
        super().__init__("binance_futures", portfolio_name, preferences_path)

        # Load auth from keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'binance_futures',
                               ['API_KEY', 'API_SECRET'])

        api_url = get_binance_url(self.preferences)
        self.__calls = Futures(key=auth.keys['API_KEY'],
                               secret=auth.keys['API_SECRET'],
                               base_url=api_url)

        self.__interface = BinanceFuturesInterface(self.exchange_type,
                                                   self.calls)

        self.initialize()

    @property
    def calls(self):
        return self.__calls

    @property
    def interface(self) -> FuturesExchangeInterface:
        return self.__interface
