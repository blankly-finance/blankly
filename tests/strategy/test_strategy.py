"""
    Unit tests for testing the strategy behaviors
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

import unittest

import blankly
from blankly import StrategyState
from blankly.utils.utils import get_quote_asset

from tests.testing_utils import get_valid_symbol


class StrategyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        pass

    def price_event(self, price, symbol, state: StrategyState):
        self.assertTrue(isinstance(price, float))

        filter_ = state.interface.get_order_filter(symbol)

        min_size = filter_['market_order']['base_min_size']

        state.interface.market_order(symbol, 'buy', min_size)

        state.interface.market_order(symbol, 'buy', min_size)

    def bar_event(self, price, symbol, state: StrategyState):
        self.assertTrue(isinstance(price, dict))
        # Check ohlcv on bar
        self.assertTrue(set(price.keys()) == {'open', 'high', 'low', 'close', 'volume'})

    def test_backtest(self):
        kwargs = {'keys_path': './tests/config/keys.json',
                  'settings_path': "./tests/config/settings.json"
                  }
        self.exchanges = [
            blankly.CoinbasePro(**kwargs),
            blankly.Binance(**kwargs),
            blankly.Oanda(**kwargs),
            blankly.Alpaca(**kwargs)
        ]

        self.strats = []
        for i in range(len(self.exchanges)):
            strategy = blankly.Strategy(self.exchanges[i])
            type_ = self.exchanges[i].interface.get_exchange_type()
            strategy.add_price_event(self.price_event, get_valid_symbol(type_), '1d')
            self.strats.append(strategy)

        for i in range(len(self.exchanges)):
            self.strats[i].backtest(to='1y', settings_path='./tests/config/backtest.json',
                                    quote_account_value_in=get_quote_asset(get_valid_symbol(
                                        self.exchanges[i].interface.get_exchange_type())))
