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
from blankly.utils.time_builder import build_day
from blankly.utils.utils import compare_dictionaries, get_base_asset, get_quote_asset
from tests.testing_utils import get_valid_symbol, forex_market_open
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface


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
    paper_trade_coinbase_pro_interface = None
    paper_trade_coinbase_pro = None
    paper_trade_binance_interface_data = None
    paper_trade_binance_data = None
    paper_trade_binance_interface = None
    paper_trade_binance = None
    FTX_Interface = None
    Oanda = None
    Oanda_Interface = None
    Alpaca_Interface = None
    alpaca = None
    Binance_data = None
    Kucoin_Interface_data = None
    Binance_Interface = None
    Binance = None
    Binance_Interface_data = None
    Kucoin_data = None
    Kucoin_Interface = None
    Coinbase_Pro_Interface = None
    Kucoin = None
    Coinbase_Pro = None
    data_interfaces = None
    interfaces = None
    FTX = None

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

        # Kucoin definition and appending
        cls.Kucoin = blankly.Kucoin(portfolio_name="KC Sandbox Portfolio",
                                    keys_path='./tests/config/keys.json',
                                    settings_path="./tests/config/settings.json")
        cls.Kucoin_Interface = cls.Kucoin.get_interface()
        cls.interfaces.append(cls.Kucoin_Interface)

        cls.Kucoin_data = blankly.Kucoin(portfolio_name="KC Data Keys",
                                         keys_path='./tests/config/keys.json',
                                         settings_path="./tests/config/settings.json")
        cls.Kucoin_Interface_data = cls.Kucoin_data.get_interface()
        cls.data_interfaces.append(cls.Kucoin_Interface_data)

        # Binance definition and appending
        cls.Binance = blankly.Binance(portfolio_name="Spot Test Key",
                                      keys_path='./tests/config/keys.json',
                                      settings_path="./tests/config/settings.json")
        cls.Binance_Interface = cls.Binance.get_interface()
        cls.interfaces.append(cls.Binance_Interface)

        # Create a Binance interface that is specifically for grabbing data
        cls.Binance_data = blankly.Binance(portfolio_name="Data Key",
                                           keys_path='./tests/config/keys.json',
                                           settings_path="./tests/config/settings.json")
        cls.Binance_Interface_data = cls.Binance_data.get_interface()
        cls.data_interfaces.append(cls.Binance_Interface_data)

        # alpaca definition and appending
        cls.alpaca = blankly.Alpaca(portfolio_name="alpaca test portfolio",
                                    keys_path='./tests/config/keys.json',
                                    settings_path="./tests/config/settings.json")
        cls.Alpaca_Interface = cls.alpaca.get_interface()
        cls.interfaces.append(cls.Alpaca_Interface)
        cls.data_interfaces.append(cls.Alpaca_Interface)

        # Oanda definition and appending
        cls.Oanda = blankly.Oanda(portfolio_name="oanda test portfolio",
                                  keys_path='./tests/config/keys.json',
                                  settings_path="./tests/config/settings.json")
        cls.Oanda_Interface = cls.Oanda.get_interface()
        cls.interfaces.append(cls.Oanda_Interface)
        cls.data_interfaces.append(cls.Oanda_Interface)
        
        cls.FTX = blankly.FTX(portfolio_name="Main Account",
                              keys_path='./tests/config/keys.json',
                              settings_path="./tests/config/settings.json")
        cls.FTX_Interface = cls.FTX.get_interface()
        cls.interfaces.append(cls.FTX_Interface)
        cls.data_interfaces.append(cls.FTX_Interface)

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
            elif self.interfaces[i].get_exchange_type() == "oanda":
                responses.append(self.interfaces[i].get_account()['USD'])
                responses.append(self.interfaces[i].get_account('USD'))
                responses.append(self.interfaces[i].account.USD)
                responses.append(self.interfaces[i].account['USD'])
            else:
                responses.append(self.interfaces[i].get_account()['BTC'])
                responses.append(self.interfaces[i].get_account('BTC'))
                responses.append(self.interfaces[i].account.BTC)
                responses.append(self.interfaces[i].account['BTC'])

                # These are just testing for error
                availability_results.append(self.interfaces[i].account.BTC.available)
                availability_results.append(self.interfaces[i].account.BTC.hold)

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def check_market_order(self, order: MarketOrder, side, size):
        """
        Test if a market order passes these checks.
        Args:
            order (dict): The market order to test - has to be type MarketOrder
            side (str): Market side (buy/sell)
            size (float): Amount of base currency used in purchase (pre-fees)
        """
        self.assertEqual(order.get_side(), side)
        self.assertEqual(order.get_size(), size)
        self.assertEqual(order.get_type(), 'market')

    def test_market_order(self):
        def check_account_delta(before: dict, after: dict, order: MarketOrder) -> None:
            # A market order should not have changed the funds on hold
            self.assertEqual(before['hold'], after['hold'])

            # The symbol should have gained less than the size on the buy if there were fees
            # Before + requested size >= the filled size
            self.assertGreaterEqual(blankly.trunc(before['available'], 2) + order.get_size(),
                                    blankly.trunc(after['available'], 2))

        # Make sure to buy back the funds we're loosing from fees - minimum balance of .1 bitcoin
        btc_account = self.Binance_Interface.get_account(symbol="BTC")['available']
        if btc_account < .1:
            self.Binance_Interface.market_order("BTC-USDT", "buy", .1)

        # These are the objects generated by blankly
        order_responses = []
        # These are the statuses that we query & check later
        status_responses = []
        # These are the immediate exchange responses that we aggregate & check
        exchange_responses = []

        for i in self.interfaces:
            type_ = i.get_exchange_type()
            if type_ == "ftx":
                continue
            if type_ == 'oanda':
                # Non fractional exchanges have to be sent here
                size = 1

                if not forex_market_open():
                    continue
            else:
                size = .01

            # Grab the account values before
            initial_value = i.get_account(get_base_asset(get_valid_symbol(type_)))

            order_responses.append({
                'order': i.market_order(get_valid_symbol(type_), 'buy', size),
                'side': 'buy',
                'size': size
            })

            # Give it half a second to execute and settle
            time.sleep(.5)

            # Grab them after
            after_value = i.get_account(get_base_asset(get_valid_symbol(type_)))
            check_account_delta(initial_value, after_value, order_responses[-1]['order'])

            order_responses.append({
                'order': i.market_order(get_valid_symbol(type_), 'sell', size),
                'side': 'sell',
                'size': size
            })

        time.sleep(.5)

        # Accumulate statuses
        for i in order_responses:
            self.check_market_order(i['order'], i['side'], i['size'])
            status_responses.append(i['order'].get_status(full=True))
            exchange_responses.append(i['order'].get_response())

        self.assertTrue(compare_responses(exchange_responses))
        self.assertTrue(compare_responses(status_responses))

        # Be sure to cancel the alpaca orders if not executed
        alpaca_orders = self.Alpaca_Interface.get_open_orders()
        for i in alpaca_orders:
            if i['type'] == "market":
                try:
                    self.Alpaca_Interface.cancel_order(i['symbol'], i['id'])
                except Exception as e:
                    print(f"Failed canceling order for reason {e} - may have already executed")

    def check_limit_order(self, limit_order: LimitOrder, expected_side: str, size, product_id):
        self.assertEqual(limit_order.get_side(), expected_side)
        self.assertEqual(limit_order.get_type(), 'limit')
        self.assertEqual(limit_order.get_time_in_force(), 'GTC')
        # TODO fix status homogeneity
        # self.assertEqual(limit_order.get_status(), {'status': 'new'})
        self.assertEqual(limit_order.get_size(), size)
        self.assertEqual(limit_order.get_symbol(), product_id)

    def test_limit_order(self):
        """
        This function tests a few components of market orders:
        - Opening market orders
        - Monitoring market orders using the order status function
        - Comparing with open orders
        - Canceling orders
        """
        limits = []
        sorted_orders = {}

        def evaluate_limit_order(interface: ABCExchangeInterface, symbol: str, buy_price: [float, int],
                                 sell_price: [float, int], size: [float, int]):
            def check_account_delta(before: dict, after: dict, order: LimitOrder) -> None:
                # On a buy the quote asset should get moved to hold
                self.assertAlmostEqual(before['available'], after['available'] + (order.get_price() * order.get_size()),
                                       places=2)

                # The symbol should have gained less than the size on the buy if there were fees
                # Before + requested size >= the filled size
                self.assertAlmostEqual(before['hold'], after['hold'] - (order.get_price() * order.get_size()),
                                       places=2)

            initial_account = interface.get_account(get_quote_asset(symbol))
            buy = interface.limit_order(symbol, 'buy', buy_price, size)
            after_buy_account = interface.get_account(get_quote_asset(symbol))
            # Buying power is always moving on alpaca, so it can't really be compared in this way
            # need a larger range
            if buy.exchange != 'alpaca':
                check_account_delta(initial_account, after_buy_account, buy)

            sell = interface.limit_order(symbol, 'sell', sell_price, size)
            self.check_limit_order(sell, 'sell', size, symbol)
            self.check_limit_order(buy,  'buy', size, symbol)

            if buy.exchange not in sorted_orders:
                sorted_orders[buy.exchange] = {}

            sorted_orders[buy.exchange] = {
                'buy': buy,
                'sell': sell
            }

            return [buy, sell]

        limits += evaluate_limit_order(self.Alpaca_Interface, 'AAPL', 10, 100000, 1)

        binance_limits = self.Binance_Interface.get_order_filter('BTC-USDT')["limit_order"]
        limits += evaluate_limit_order(self.Binance_Interface, 'BTC-USDT', int(binance_limits['min_price']+100),
                                       int(binance_limits['max_price']-100), .01)

        limits += evaluate_limit_order(self.Coinbase_Pro_Interface, 'BTC-USD', .01, 100000, 1)

        limits += evaluate_limit_order(self.Kucoin_Interface, 'ETH-USDT', .01, 100000, 1)

        limits += evaluate_limit_order(self.Oanda_Interface, 'EUR-USD', .01, 100000, 1)

        responses = []
        status = []
        cancels = []

        open_orders = {
            'coinbase_pro': self.Coinbase_Pro_Interface.get_open_orders('BTC-USD'),
            'binance': self.Binance_Interface.get_open_orders('BTC-USDT'),
            'kucoin': self.Kucoin_Interface.get_open_orders('ETH-USDT'),
            'alpaca': self.Alpaca_Interface.get_open_orders('AAPL'),
            'oanda': self.Oanda_Interface.get_open_orders('EUR-USD')
        }

        # Simple test to ensure that some degree of orders have been placed
        for i in open_orders:
            self.assertTrue(len(open_orders[i]) >= 2)

        # Just scan through both simultaneously to reduce code copying
        all_orders = open_orders['coinbase_pro']
        all_orders = all_orders + open_orders['binance']
        all_orders = all_orders + open_orders['kucoin']
        all_orders = all_orders + open_orders['alpaca']
        all_orders = all_orders + open_orders['oanda']

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

        cancels.append(self.Binance_Interface.cancel_order('BTC-USDT', sorted_orders['binance']['buy'].get_id()))
        cancels.append(self.Binance_Interface.cancel_order('BTC-USDT', sorted_orders['binance']['sell'].get_id()))

        cancels.append(self.Kucoin_Interface.cancel_order('ETH-USDT', sorted_orders['kucoin']['buy'].get_id()))
        cancels.append(self.Kucoin_Interface.cancel_order('ETH-USDT', sorted_orders['kucoin']['sell'].get_id()))

        cancels.append(self.Coinbase_Pro_Interface.cancel_order('BTC-USD',
                                                                sorted_orders['coinbase_pro']['buy'].get_id()))
        cancels.append(self.Coinbase_Pro_Interface.cancel_order('BTC-USD',
                                                                sorted_orders['coinbase_pro']['sell'].get_id()))

        cancels.append(self.Alpaca_Interface.cancel_order('AAPL', sorted_orders['alpaca']['buy'].get_id()))
        cancels.append(self.Alpaca_Interface.cancel_order('AAPL', sorted_orders['alpaca']['sell'].get_id()))

        cancels.append(self.Oanda_Interface.cancel_order('EUR-USD', sorted_orders['oanda']['buy'].get_id()))
        cancels.append(self.Oanda_Interface.cancel_order('EUR-USD', sorted_orders['oanda']['sell'].get_id()))

        self.assertTrue(compare_responses(cancels, force_exchange_specific=False))

    def test_get_keys(self):
        responses = []
        for i in self.interfaces:
            responses.append(i.get_fees())

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def check_product_history_types(self, df: pd.DataFrame):
        # This is caused by casting on windows in pandas - I believe it is a bug
        self.assertTrue(isinstance(df['time'].iloc[0], int) or
                        isinstance(df['time'].iloc[0], numpy.int64) or
                        isinstance(df['time'].iloc[0], numpy.int32))
        self.assertTrue(isinstance(df['low'].iloc[0], float))
        self.assertTrue(isinstance(df['high'].iloc[0], float))
        self.assertTrue(isinstance(df['open'].iloc[0], float))
        self.assertTrue(isinstance(df['close'].iloc[0], float))
        self.assertTrue(isinstance(df['volume'].iloc[0], float))

    def check_product_history_columns(self, df: pd.DataFrame):
        self.assertTrue(isinstance(df['time'], pd.Series))
        self.assertTrue(isinstance(df['low'], pd.Series))
        self.assertTrue(isinstance(df['high'], pd.Series))
        self.assertTrue(isinstance(df['open'], pd.Series))
        self.assertTrue(isinstance(df['close'], pd.Series))
        self.assertTrue(isinstance(df['volume'], pd.Series))
    
    def test_single_point_history(self):
        for i in self.data_interfaces:
            print(f'Checking {i.get_exchange_type()}')
            valid_symbol = get_valid_symbol(i.get_exchange_type())
            response = i.history(valid_symbol, 1)

            self.check_product_history_columns(response)

            self.assertEqual(len(response), 1)

            self.check_product_history_types(response)

    def test_point_based_history(self):
        for i in self.data_interfaces:
            valid_symbol = get_valid_symbol(i.get_exchange_type())
            response = i.history(valid_symbol, 150, resolution='1d')

            print(f'Checking {i.get_exchange_type()}')
            self.check_product_history_columns(response)

            self.assertEqual(150, len(response))

            self.check_product_history_types(response)

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
                valid_symbol = get_valid_symbol(i.get_exchange_type())
                responses.append((i.history(valid_symbol,
                                            to=expected_hours,
                                            resolution='1h',
                                            end_date=end_date_str),
                                  i.get_exchange_type()))
        for i in responses:
            self.check_product_history_columns(i[0])

            last_date = dt.fromtimestamp(i[0]['time'].iloc[-1]).strftime('%Y-%m-%d')
            self.assertEqual(close_stop, last_date)

            self.check_product_history_types(i[0])

    def test_start_with_end_history(self):
        responses = []

        # This initial selection could fail because of the slightly random day that they delete their data
        stop_dt = dateparser.parse("2021-08-04")
        start = "2021-01-07"
        stop = str(stop_dt.date())

        # The dates are offset by one because the time is the open time
        close_stop = str(stop_dt.replace(day=stop_dt.day-1).date())

        for i in self.data_interfaces:
            valid_symbol = get_valid_symbol(i.get_exchange_type())
            responses.append(i.history(valid_symbol, resolution='1h', start_date=start, end_date=stop))

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
        intervals_ago = time.time() - (build_day() * test_intervals)

        responses = []
        for i in self.data_interfaces:
            type_ = i.get_exchange_type()

            # Exclude alpaca currently because the trading hours make it unreliable
            if not (type_ == "alpaca" or type_ == 'oanda'):
                responses.append(i.get_product_history(get_valid_symbol(type_),
                                                       intervals_ago,
                                                       current_time,
                                                       build_day()))
            else:
                # These are the open/close market hours exchanges
                response = (i.get_product_history(get_valid_symbol(type_),
                                                  intervals_ago,
                                                  current_time,
                                                  build_day()))
                self.check_product_history_columns(response)
                self.check_product_history_types(response)

        for i in responses:
            self.check_product_history_columns(i)

            self.assertEqual(len(i), test_intervals)
            start_time = i['time'][0]
            end_time = i['time'].iloc[-1]

            # Make sure that the final time we have is within the resolution window. Notice this is shifted backwards
            self.assertTrue(current_time-(build_day()) < end_time < current_time,
                            f"\ncurrent_time-(build_day()): {current_time-(build_day())}\nend_time: "
                            f"{end_time}\ncurrent_time: {current_time}\n")

            # Do the same, the start time has to be within a resolution interval of the actual time
            # This is shifted forward
            self.assertTrue(intervals_ago < start_time < intervals_ago+(build_day()))

            self.check_product_history_types(i)

    def test_get_order_filter(self):
        responses = []
        types = []
        for i in self.interfaces:
            type_ = i.get_exchange_type()
            types.append(type_)
            responses.append(i.get_order_filter(get_valid_symbol(type_)))

        self.assertTrue(compare_responses(responses))

    def test_get_price(self):
        responses = []

        for i in self.interfaces:
            type_ = i.get_exchange_type()
            responses.append(i.get_price(get_valid_symbol(type_)))

        for i in responses:
            self.assertTrue(isinstance(i, float))