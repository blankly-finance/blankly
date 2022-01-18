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
from blankly.utils.utils import compare_dictionaries
from tests.testing_utils import get_valid_symbol


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

        # Kucoin definition and appending
        cls.Kucoin = blankly.Kucoin(portfolio_name="KC Sandbox Portfolio",
                                    keys_path='./tests/config/keys.json',
                                    settings_path="./tests/config/settings.json")
        cls.Kucoin_Interface = cls.Kucoin.get_interface()
        cls.interfaces.append(cls.Kucoin_Interface)

        cls.Kucoin_data = blankly.Kucoin(portfolio_name="KC Data Keys",
                                         keys_path='./tests/config/keys.json',
                                         settings_path="./tests/config/settings_live_enabled.json")
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
            if not (type_ == 'alpaca' or type_ == 'oanda'):
                size = .01
            else:
                # Non fractional exchanges have to be sent here
                size = 1

            order_responses.append({
                'order': i.market_order(get_valid_symbol(type_), 'buy', size),
                'side': 'buy',
                'size': size
            })

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

        binance_buy = self.Binance_Interface.limit_order('BTC-USDT', 'buy', int(binance_limits['min_price']+100), .01)
        binance_sell = self.Binance_Interface.limit_order('BTC-USDT', 'sell', int(binance_limits['max_price']-100), .01)
        self.check_limit_order(binance_sell, 'sell', .01, 'BTC-USDT')
        self.check_limit_order(binance_buy, 'buy', .01, 'BTC-USDT')
        time.sleep(3)

        coinbase_buy = self.Coinbase_Pro_Interface.limit_order('BTC-USD', 'buy', .01, 1)
        self.check_limit_order(coinbase_buy, 'buy', 1, 'BTC-USD')

        coinbase_sell = self.Coinbase_Pro_Interface.limit_order('BTC-USD', 'sell', 100000, 1)
        self.check_limit_order(coinbase_sell, 'sell', 1, 'BTC-USD')

        kucoin_buy = self.Kucoin_Interface.limit_order('ETH-USDT', 'buy', .01, 1)
        self.check_limit_order(kucoin_buy, 'buy', 1, 'ETH-USDT')

        kucoin_sell = self.Kucoin_Interface.limit_order('ETH-USDT', 'sell', 100000, 1)
        self.check_limit_order(kucoin_sell, 'sell', 1, 'ETH-USDT')

        alpaca_buy = self.Alpaca_Interface.limit_order('AAPL', 'buy', 10, 1)
        self.check_limit_order(alpaca_buy, 'buy', 1, 'AAPL')

        alpaca_sell = self.Alpaca_Interface.limit_order('AAPL', 'sell', 100000, 1)
        self.check_limit_order(alpaca_sell, 'sell', 1, 'AAPL')

        oanda_buy = self.Oanda_Interface.limit_order('EUR-USD', 'buy', .01, 1)
        self.check_limit_order(oanda_buy, 'buy', 1, 'EUR-USD')

        oanda_sell = self.Oanda_Interface.limit_order('EUR-USD', 'sell', 100000, 1)
        self.check_limit_order(oanda_sell, 'sell', 1, 'EUR-USD')

        limits = [binance_buy, binance_sell, coinbase_buy, coinbase_sell, kucoin_buy, kucoin_sell,
                  alpaca_sell, alpaca_buy, oanda_buy, oanda_sell]
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

        cancels.append(self.Binance_Interface.cancel_order('BTC-USDT', binance_buy.get_id()))
        cancels.append(self.Binance_Interface.cancel_order('BTC-USDT', binance_sell.get_id()))

        cancels.append(self.Kucoin_Interface.cancel_order('ETH-USDT', kucoin_buy.get_id()))
        cancels.append(self.Kucoin_Interface.cancel_order('ETH-USDT', kucoin_sell.get_id()))

        cancels.append(self.Coinbase_Pro_Interface.cancel_order('BTC-USD', coinbase_sell.get_id()))
        cancels.append(self.Coinbase_Pro_Interface.cancel_order('BTC-USD', coinbase_buy.get_id()))

        cancels.append(self.Alpaca_Interface.cancel_order('AAPL', alpaca_buy.get_id()))
        cancels.append(self.Alpaca_Interface.cancel_order('AAPL', alpaca_sell.get_id()))

        cancels.append(self.Oanda_Interface.cancel_order('EUR-USD', oanda_buy.get_id()))
        cancels.append(self.Oanda_Interface.cancel_order('EUR-USD', oanda_sell.get_id()))

        self.assertTrue(compare_responses(cancels, force_exchange_specific=False))

    def test_get_keys(self):
        responses = []
        for i in self.interfaces:
            responses.append(i.get_fees())

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def check_product_history_types(self, df: pd.DataFrame):
        # This is caused by casting on windows in pandas - I believe it is a bug
        self.assertTrue(isinstance(df['time'][0], int) or
                        isinstance(df['time'][0], numpy.int64) or
                        isinstance(df['time'][0], numpy.int32))
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
            valid_symbol = get_valid_symbol(i.get_exchange_type())
            responses.append(i.history(valid_symbol, 1))

        for i in responses:
            self.check_product_history_columns(i)

            self.assertEqual(len(i), 1)

            self.check_product_history_types(i)

    def test_point_based_history(self):
        responses = []
        for i in self.data_interfaces:
            valid_symbol = get_valid_symbol(i.get_exchange_type())
            responses.append(i.history(valid_symbol, 150, resolution='1d'))
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
            # TODO add separate tests for trading hours exchanges (for now they're just run and types checked)
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
