"""
    Unit test class to ensure that each exchange gives the same result with the same types.
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

import time
import unittest
from datetime import datetime as dt

import dateparser
import numpy
import pandas as pd

import blankly
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils.time_builder import build_hour
from blankly.utils.utils import compare_dictionaries


def compare_responses(response_list, force_exchange_specific=True):
    """
    Compare a set of responses against the others. This supports a large set of interfaces
    """
    for i in range(len(response_list) - 1):
        if not compare_dictionaries(response_list[i], response_list[i + 1], force_exchange_specific):
            print("Failed checking index " + str(i + 1) + " against index " + str(i))
            return False
    return True


class InterfaceHomogeneity(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.interfaces = []
        cls.data_interfaces = []

        # Coinbase Pro definition and appending
        cls.Coinbase_Pro = blankly.CoinbasePro(portfolio_name="Sandbox Portfolio",
                                               keys_path='./tests/config/keys.json',
                                               settings_path="./tests/config/settings.json")
        cls.Coinbase_Pro_Interface = cls.Coinbase_Pro.get_interface()
        cls.interfaces.append(cls.Coinbase_Pro_Interface)
        cls.data_interfaces.append(cls.Coinbase_Pro_Interface)

        # Binance definition and appending
        cls.Binance = blankly.Binance(portfolio_name="Spot Test Key",
                                      keys_path='./tests/config/keys.json',
                                      settings_path="./tests/config/settings.json")
        cls.Binance_Interface = cls.Binance.get_interface()
        cls.interfaces.append(cls.Binance_Interface)

        # Create a Binance interface that is specifically for grabbing data
        cls.Binance_data = blankly.Binance(portfolio_name="Data Key",
                                           keys_path='./tests/config/keys.json',
                                           settings_path="./tests/config/settings_live_enabled.json")
        cls.Binance_Interface_data = cls.Binance_data.get_interface()
        cls.data_interfaces.append(cls.Binance_Interface_data)

        # alpaca definition and appending
        cls.alpaca = blankly.Alpaca(portfolio_name="alpaca test portfolio",
                                    keys_path='./tests/config/keys.json',
                                    settings_path="./tests/config/settings.json")
        cls.Alpaca_Interface = cls.alpaca.get_interface()
        cls.interfaces.append(cls.Alpaca_Interface)
        cls.data_interfaces.append(cls.Alpaca_Interface)

        # Paper trade wraps binance
        cls.paper_trade_binance = blankly.PaperTrade(cls.Binance)
        cls.paper_trade_binance_interface = cls.paper_trade_binance.get_interface()
        cls.interfaces.append(cls.paper_trade_binance_interface)

        # Create another for data keys
        cls.paper_trade_binance_data = blankly.PaperTrade(cls.Binance_data)
        cls.paper_trade_binance_interface_data = cls.paper_trade_binance_data.get_interface()
        cls.data_interfaces.append(cls.paper_trade_binance_interface_data)

        # Another wraps coinbase pro
        cls.paper_trade_coinbase_pro = blankly.PaperTrade(cls.Coinbase_Pro)
        cls.paper_trade_coinbase_pro_interface = cls.paper_trade_coinbase_pro.get_interface()
        cls.interfaces.append(cls.paper_trade_coinbase_pro_interface)
        cls.data_interfaces.append(cls.paper_trade_coinbase_pro_interface)

    def test_get_products(self):
        responses = []
        for i in range(len(self.interfaces)):
            responses.append(self.interfaces[i].get_products()[0])

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def test_get_account(self):
        responses = []

        availability_results = []

        for i in range(len(self.interfaces)):
            if self.interfaces[i].get_exchange_type() == "alpaca":
                responses.append(self.interfaces[i].get_account()['AAPL'])
                responses.append(self.interfaces[i].get_account('AAPL'))
                responses.append(self.interfaces[i].account.AAPL)
                responses.append(self.interfaces[i].account['AAPL'])

                # These are just testing for error
                availability_results.append(self.interfaces[i].account.AAPL.available)
                availability_results.append(self.interfaces[i].account.AAPL.hold)
            else:
                responses.append(self.interfaces[i].get_account()['BTC'])
                responses.append(self.interfaces[i].get_account('BTC'))
                responses.append(self.interfaces[i].account.BTC)
                responses.append(self.interfaces[i].account['BTC'])

                # These are just testing for error
                availability_results.append(self.interfaces[i].account.BTC.available)
                availability_results.append(self.interfaces[i].account.BTC.hold)

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def check_market_order(self, order1: MarketOrder, side, size):
        """
        Test if a market order passes these checks.
        Args:
            order1 (dict): The market order to test - has to be type MarketOrder
            side (str): Market side (buy/sell)
            size (float): Amount of base currency used in purchase (pre-fees)
        """
        self.assertEqual(order1.get_side(), side)
        self.assertEqual(order1.get_size(), size)
        self.assertEqual(order1.get_type(), 'market')

    def test_market_order(self):
        # Make sure to buy back the funds we're loosing from fees - minimum balance of .1 bitcoin
        btc_account = self.Binance_Interface.get_account(symbol="BTC")['available']
        if btc_account < .1:
            self.Binance_Interface.market_order("BTC-USDT", "buy", .1)

        binance_buy = self.Binance_Interface.market_order('BTC-USDT', 'buy', .01)
        binance_sell = self.Binance_Interface.market_order('BTC-USDT', 'sell', .01)

        self.check_market_order(binance_buy, 'buy', .01)
        self.check_market_order(binance_sell, 'sell', .01)

        self.assertTrue(compare_dictionaries(binance_buy.get_response(), binance_sell.get_response()))
        time.sleep(.5)
        self.assertTrue(compare_dictionaries(binance_buy.get_status(full=True), binance_sell.get_status(full=True)))

        coinbase_buy = self.Coinbase_Pro_Interface.market_order('BTC-USD', 'buy', .01)
        coinbase_sell = self.Coinbase_Pro_Interface.market_order('BTC-USD', 'sell', .01)

        self.assertTrue(compare_dictionaries(coinbase_buy.get_response(), coinbase_sell.get_response()))
        self.assertTrue(compare_dictionaries(coinbase_buy.get_status(full=True), coinbase_sell.get_status(full=True)))

        alpaca_buy = self.Alpaca_Interface.market_order('AAPL', 'buy', 1)
        alpaca_sell = self.Alpaca_Interface.market_order('AAPL', 'sell', 1)

        self.assertTrue(compare_dictionaries(alpaca_buy.get_response(), alpaca_buy.get_response()))
        self.assertTrue(compare_dictionaries(alpaca_sell.get_status(full=True), alpaca_sell.get_status(full=True)))

        response_list = [coinbase_buy.get_response(),
                         coinbase_sell.get_response(),
                         binance_buy.get_response(),
                         binance_sell.get_response(),
                         alpaca_buy.get_response(),
                         alpaca_sell.get_response()
                         ]

        time.sleep(1)

        status_list = [coinbase_buy.get_status(full=True),
                       coinbase_sell.get_status(full=True),
                       binance_buy.get_status(full=True),
                       binance_sell.get_status(full=True),
                       alpaca_buy.get_status(full=True),
                       alpaca_sell.get_status(full=True)
                       ]

        self.assertTrue(compare_responses(response_list))

        self.assertTrue(compare_responses(status_list))

        # Be sure to cancel the alpaca orders if not executed
        alpaca_orders = self.Alpaca_Interface.get_open_orders()
        for i in alpaca_orders:
            if i['type'] == "market":
                try:
                    self.Alpaca_Interface.cancel_order(i['symbol'], i['id'])
                except Exception:
                    print("Failed canceling order - may have already executed")

    def check_limit_order(self, limit_order: LimitOrder, expected_side: str, size, product_id):
        self.assertEqual(limit_order.get_side(), expected_side)
        self.assertEqual(limit_order.get_type(), 'limit')
        self.assertEqual(limit_order.get_time_in_force(), 'GTC')
        # TODO fix status homogeneity
        # self.assertEqual(limit_order.get_status(), {'status': 'new'})
        self.assertEqual(limit_order.get_size(), size)
        self.assertEqual(limit_order.get_asset_id(), product_id)

    def test_limit_order(self):
        """
        This function tests a few components of market orders:
        - Opening market orders
        - Monitoring market orders using the order status function
        - Comparing with open orders
        - Canceling orders
        """
        binance_limits = self.Binance_Interface.get_order_filter('BTC-USDT')["limit_order"]

        binance_buy = self.Binance_Interface.limit_order('BTC-USDT', 'buy', int(binance_limits['min_price']+30), .01)
        time.sleep(3)
        self.check_limit_order(binance_buy, 'buy', .01, 'BTC-USDT')

        coinbase_buy = self.Coinbase_Pro_Interface.limit_order('BTC-USD', 'buy', .01, 1)
        self.check_limit_order(coinbase_buy, 'buy', 1, 'BTC-USD')

        binance_sell = self.Binance_Interface.limit_order('BTC-USDT', 'sell', int(binance_limits['max_price']-30), .01)
        self.check_limit_order(binance_sell, 'sell', .01, 'BTC-USDT')

        coinbase_sell = self.Coinbase_Pro_Interface.limit_order('BTC-USD', 'sell', 100000, 1)
        self.check_limit_order(coinbase_sell, 'sell', 1, 'BTC-USD')

        alpaca_buy = self.Alpaca_Interface.limit_order('AAPL', 'buy', 10, 1)
        self.check_limit_order(alpaca_buy, 'buy', 1, 'AAPL')

        alpaca_sell = self.Alpaca_Interface.limit_order('AAPL', 'sell', 1000000000, 1)
        self.check_limit_order(alpaca_sell, 'sell', 1, 'AAPL')

        limits = [binance_buy, binance_sell, coinbase_buy, coinbase_sell, alpaca_sell, alpaca_buy]
        responses = []
        status = []

        cancels = []

        # Just scan through both simultaneously to reduce code copying
        all_orders = self.Coinbase_Pro_Interface.get_open_orders('BTC-USD')
        all_orders = all_orders + self.Binance_Interface.get_open_orders('BTC-USDT')
        all_orders = all_orders + self.Alpaca_Interface.get_open_orders('AAPL')

        # Filter for limit orders
        open_orders = []
        for i in all_orders:
            if i['type'] == 'limit':
                open_orders.append(i)

        self.assertTrue(compare_responses(open_orders))
        for i in limits:
            found = False
            for j in open_orders:
                if i.get_id() == j['id']:
                    found = True
                    self.assertTrue(compare_dictionaries(i.get_response(), j))
                    break
            self.assertTrue(found)

        for i in limits:
            responses.append(i.get_response())
            status.append(i.get_status(full=True))

        self.assertTrue(compare_responses(responses))
        self.assertTrue(compare_responses(status))

        cancels.append(self.Binance_Interface.cancel_order('BTC-USDT', binance_buy.get_id()))
        cancels.append(self.Binance_Interface.cancel_order('BTC-USDT', binance_sell.get_id()))

        cancels.append(self.Coinbase_Pro_Interface.cancel_order('BTC-USD', coinbase_sell.get_id()))
        cancels.append(self.Coinbase_Pro_Interface.cancel_order('BTC-USD', coinbase_buy.get_id()))

        cancels.append(self.Alpaca_Interface.cancel_order('AAPL', alpaca_buy.get_id()))
        cancels.append(self.Alpaca_Interface.cancel_order('AAPL', alpaca_sell.get_id()))

        self.assertTrue(compare_responses(cancels, force_exchange_specific=False))

    def test_get_keys(self):
        responses = []
        for i in self.interfaces:
            responses.append(i.get_fees())

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def check_product_history_types(self, df: pd.DataFrame):
        self.assertTrue(isinstance(df['time'][0], numpy.int64))
        self.assertTrue(isinstance(df['low'][0], float))
        self.assertTrue(isinstance(df['high'][0], float))
        self.assertTrue(isinstance(df['open'][0], float))
        self.assertTrue(isinstance(df['close'][0], float))
        self.assertTrue(isinstance(df['volume'][0], float))

    def check_product_history_columns(self, df: pd.DataFrame):
        self.assertTrue(isinstance(df['time'], pd.Series))
        self.assertTrue(isinstance(df['low'], pd.Series))
        self.assertTrue(isinstance(df['high'], pd.Series))
        self.assertTrue(isinstance(df['open'], pd.Series))
        self.assertTrue(isinstance(df['close'], pd.Series))
        self.assertTrue(isinstance(df['volume'], pd.Series))
    
    def test_single_point_history(self):
        responses = []
        for i in self.data_interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.history('BTC-USDT', 1))
            elif i.get_exchange_type() == "alpaca":
                responses.append(i.history('MSFT', 1))
            else:
                responses.append(i.history('BTC-USD', 1))

        for i in responses:
            self.check_product_history_columns(i)

            self.assertEqual(len(i), 1)

            self.check_product_history_types(i)

    def test_point_based_history(self):
        responses = []
        for i in self.data_interfaces:
            print(i.get_exchange_type())
            if i.get_exchange_type() == "binance":
                responses.append(i.history('BTC-USDT', 150, resolution='1h'))
            elif i.get_exchange_type() == "alpaca":
                responses.append(i.history('MSFT', 150, resolution='1h'))
            else:
                # Test this one a 1 day resolution due to low volume
                responses.append(i.history('BTC-USD', 150, resolution='1d'))
        for i in responses:
            self.check_product_history_columns(i)

            self.assertEqual(150, len(i))

            self.check_product_history_types(i)

    def test_point_with_end_history(self):
        responses = []

        arbitrary_date: dt = dateparser.parse("8/23/21")

        # This won't work at the start of the
        end_date = arbitrary_date.replace(day=arbitrary_date.day-1)
        close_stop = str(arbitrary_date.replace(day=arbitrary_date.day-2).date())

        expected_hours = end_date.day * 24 - (24*2)

        end_date_str = str(end_date.date())

        # This won't run until the fourth day of the month because of binance
        if arbitrary_date.month == end_date.month - 1:
            for i in self.data_interfaces:
                if i.get_exchange_type() == "binance":
                    responses.append((i.history('BTC-USDT', to=expected_hours, resolution='1h', end_date=end_date_str),
                                      'binance'))
                elif i.get_exchange_type() == "alpaca":
                    responses.append((i.history('MSFT', to=expected_hours, resolution='1h', end_date=end_date_str),
                                      'alpaca'))
                else:
                    responses.append((i.history('BTC-USD', to=expected_hours, resolution='1h', end_date=end_date_str),
                                      'coinbase_pro'))
        for i in responses:
            self.check_product_history_columns(i[0])

            last_date = dt.fromtimestamp(i[0]['time'].iloc[-1]).strftime('%Y-%m-%d')
            self.assertEqual(close_stop, last_date)

            self.check_product_history_types(i[0])

    def test_start_with_end_history(self):
        responses = []

        # This initial selection could fail because of the slightly random day that they delete their data
        stop_dt = dateparser.parse("2021-08-04")
        start = "2021-01-04"
        stop = str(stop_dt.date())

        # The dates are offset by one because the time is the open time
        close_stop = str(stop_dt.replace(day=stop_dt.day-1).date())

        for i in self.data_interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.history('BTC-USDT', resolution='1h', start_date=start, end_date=stop))
            elif i.get_exchange_type() == "alpaca":
                responses.append(i.history('MSFT', resolution='1h', start_date=start, end_date=stop))
            else:
                responses.append(i.history('BTC-USD', resolution='1h', start_date=start, end_date=stop))

        for idx, resp in enumerate(responses):
            start_date = dt.fromtimestamp(resp['time'][0]).strftime('%Y-%m-%d')
            end_date = dt.fromtimestamp(resp['time'].iloc[-1]).strftime('%Y-%m-%d')

            print("Homogeneity test started on interface: " + self.interfaces[idx].get_exchange_type())
            self.check_product_history_columns(resp)
            self.assertEqual(start_date, start)
            self.assertEqual(end_date, close_stop)

    def test_get_product_history(self):
        # Setting for number of hours to test backwards to
        test_intervals = 100

        current_time = time.time()
        current_date = dt.fromtimestamp(current_time).strftime('%Y-%m-%d')
        intervals_ago = time.time() - (build_hour() * test_intervals)
        intervals_ago_date = dt.fromtimestamp(intervals_ago).strftime('%Y-%m-%d')

        responses = []
        for i in self.data_interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.get_product_history('BTC-USDT', intervals_ago, current_time, 3600))
            elif i.get_exchange_type() == "alpaca":
                # Alpaca has trading hours :(
                # responses.append(i.get_product_history('MSFT', intervals_ago, current_time, 3600))
                pass
            else:
                # Coinbase pro has low volume hours on the sandbox exchange
                # responses.append(i.get_product_history('BTC-USD', intervals_ago, current_time, build_hour()))
                pass

        for i in responses:
            self.check_product_history_columns(i)

            self.assertEqual(len(i), test_intervals)
            start_date = dt.fromtimestamp(i['time'][0]).strftime('%Y-%m-%d')
            end_date = dt.fromtimestamp(i['time'].iloc[-1]).strftime('%Y-%m-%d')

            self.assertEqual(start_date, intervals_ago_date)
            self.assertEqual(end_date, current_date)

            self.check_product_history_types(i)

    def test_get_order_filter(self):
        responses = []

        for i in self.interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.get_order_filter('BTC-USDT'))
            elif i.get_exchange_type() == "alpaca":
                responses.append(i.get_order_filter('MSFT'))
            else:
                responses.append(i.get_order_filter('BTC-USD'))

        self.assertTrue(compare_responses(responses))

    def test_get_price(self):
        responses = []

        for i in self.interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.get_price('BTC-USDT'))
            elif i.get_exchange_type() == "alpaca":
                responses.append(i.get_price('MSFT'))
            else:
                responses.append(i.get_price('BTC-USD'))

        for i in responses:
            self.assertTrue(isinstance(i, float))
