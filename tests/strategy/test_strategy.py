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
        cls.ran_price_event = False
        cls.ran_bar_event = False

    def price_event(self, price, symbol, state: StrategyState):
        self.assertTrue(isinstance(price, float))

        filter_ = state.interface.get_order_filter(symbol)

        min_size = filter_['market_order']['base_min_size']

        # Ensure you check for ints
        if min_size == 1.0:
            min_size = 1

        state.interface.market_order(symbol, 'buy', min_size)

        state.interface.market_order(symbol, 'buy', min_size)

        self.ran_price_event = True

    def bar_event(self, price, symbol, state: StrategyState):
        self.assertTrue(isinstance(price, dict))
        # Check ohlcv on bar
        self.assertTrue(set(price.keys()) == {'open', 'high', 'low', 'close', 'volume'})
        self.ran_bar_event = True

    def test_backtest(self):
        kwargs = {'keys_path': './tests/config/keys.json',
                  'settings_path': "./tests/config/settings.json"}

        self.exchanges = [
            blankly.Kucoin(**kwargs),
            blankly.FTX(**kwargs),
            blankly.CoinbasePro(**kwargs),
            blankly.Binance(**kwargs),
            blankly.Oanda(**kwargs),
            blankly.Alpaca(**kwargs)
        ]

        for i in range(len(self.exchanges)):
            strategy = blankly.Strategy(self.exchanges[i])
            type_ = self.exchanges[i].interface.get_exchange_type()
            strategy.add_price_event(self.price_event, get_valid_symbol(type_), '1d')
            strategy.add_bar_event(self.bar_event, get_valid_symbol(type_), '1d')
            print(f'Associated {get_valid_symbol(type_)} with {type_}.')

            print(f"Testing: {self.exchanges[i].interface.get_exchange_type()} without benchmark")
            quote_asset = get_quote_asset(get_valid_symbol(self.exchanges[i].interface.get_exchange_type()))
            strategy.backtest(to='1y', settings_path='./tests/config/backtest.json',
                              quote_account_value_in=quote_asset,
                              initial_values={quote_asset: 1000000000},
                              benchmark_symbol=None,
                              continuous_caching=False)
            # Of course, it'll pass if the function never runs, make sure it does
            assert self.ran_price_event
            self.ran_price_event = False
            assert self.ran_bar_event
            self.ran_bar_event = False
            print(f"Testing: {self.exchanges[i].interface.get_exchange_type()} with benchmark")
            strategy.backtest(to='1y', settings_path='./tests/config/backtest.json',
                              quote_account_value_in=get_quote_asset(get_valid_symbol(
                                        self.exchanges[i].interface.get_exchange_type())),
                              benchmark_symbol=get_valid_symbol(self.exchanges[i].interface.get_exchange_type()),
                              initial_values={quote_asset: 1000000000},
                              continuous_caching=False)
            assert self.ran_price_event
            self.ran_price_event = False
            assert self.ran_bar_event
            self.ran_bar_event = False
