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


import Blankly
from Blankly.utils.utils import compare_dictionaries
from Blankly.utils.time_builder import build_hour
import unittest
import time
import pandas as pd
import numpy

from Blankly.exchanges.orders.market_order import MarketOrder
from Blankly.exchanges.orders.limit_order import LimitOrder


def compare_responses(response_list, force_exchange_specific=True):
    """
    Compare a set of responses against the others. This supports a large set of interfaces
    """
    for i in range(len(response_list)-1):
        if not compare_dictionaries(response_list[i], response_list[i+1], force_exchange_specific):
            print("Failed checking index " + str(i+1) + " against index " + str(i))
            return False
    return True


class InterfaceHomogeneity(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.interfaces = []

        # Coinbase Pro definition and appending
        cls.Coinbase_Pro = Blankly.CoinbasePro(portfolio_name="Sandbox Portfolio",
                                               keys_path='./tests/config/keys.json',
                                               settings_path="./tests/config/settings.json")
        cls.Coinbase_Pro_Interface = cls.Coinbase_Pro.get_interface()
        cls.interfaces.append(cls.Coinbase_Pro_Interface)

        # binance definition and appending
        cls.Binance = Blankly.Binance(portfolio_name="Spot Test Key",
                                      keys_path='./tests/config/keys.json',
                                      settings_path="./tests/config/settings.json")
        cls.Binance_Interface = cls.Binance.get_interface()
        cls.interfaces.append(cls.Binance_Interface)

        # alpaca definition and appending
        # cls.alpaca = Blankly.alpaca(portfolio_name="alpaca test portfolio",
        #                             keys_path='./tests/config/keys.json',
        #                             settings_path="./tests/config/settings.json")
        # cls.Alpaca_Interface = cls.alpaca.get_interface()
        # cls.Interfaces.append(cls.Alpaca_Interface)

        # Paper trade wraps binance
        cls.paper_trade_binance = Blankly.PaperTrade(cls.Binance)
        cls.paper_trade_binance_interface = cls.paper_trade_binance.get_interface()
        cls.interfaces.append(cls.paper_trade_binance_interface)

        # Another wraps coinbase pro
        cls.paper_trade_coinbase_pro = Blankly.PaperTrade(cls.Coinbase_Pro)
        cls.paper_trade_coinbase_pro_interface = cls.paper_trade_coinbase_pro.get_interface()
        cls.interfaces.append(cls.paper_trade_coinbase_pro_interface)

    def test_get_products(self):
        responses = []
        for i in range(len(self.interfaces)):
            responses.append(self.interfaces[i].get_products()[0])

        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def test_get_account(self):
        responses = []
        for i in range(len(self.interfaces)):
            responses.append(self.interfaces[i].get_account()['BTC'])
        self.assertTrue(compare_responses(responses, force_exchange_specific=False))

    def check_market_order(self, order1: MarketOrder, side, funds):
        """
        Test if a market order passes these checks.
        Args:
            order1 (dict): The market order to test - has to be type MarketOrder
            side (str): Market side (buy/sell)
            funds (float): Amount of money used in purchase (pre-fees)
        """
        self.assertEqual(order1.get_side(), side)
        self.assertLess(order1.get_funds(), funds)
        self.assertEqual(order1.get_type(), 'market')

    def test_market_order(self):
        # Make sure to buy back the funds we're loosing from fees - minimum balance of .1 bitcoin
        btc_account = self.Binance_Interface.get_account(symbol="BTC")['available']
        if btc_account < .1:
            price = self.Binance_Interface.get_price("BTC-USDT")
            self.Binance_Interface.market_order("BTC-USDT", "buy", price * .1)

        binance_buy = self.Binance_Interface.market_order('BTC-USDT', 'buy', 20)
        binance_sell = self.Binance_Interface.market_order('BTC-USDT', 'sell', 20)

        self.check_market_order(binance_buy, 'buy', 20)
        self.check_market_order(binance_sell, 'sell', 20)

        self.assertTrue(compare_dictionaries(binance_buy.get_response(), binance_sell.get_response()))
        self.assertTrue(compare_dictionaries(binance_buy.get_status(full=True), binance_sell.get_status(full=True)))

        coinbase_buy = self.Coinbase_Pro_Interface.market_order('BTC-USD', 'buy', 20)
        coinbase_sell = self.Coinbase_Pro_Interface.market_order('BTC-USD', 'sell', 20)

        self.assertTrue(compare_dictionaries(coinbase_buy.get_response(), coinbase_sell.get_response()))
        self.assertTrue(compare_dictionaries(coinbase_buy.get_status(full=True), coinbase_sell.get_status(full=True)))

        response_list = [coinbase_buy.get_response(),
                         coinbase_sell.get_response(),
                         binance_buy.get_response(),
                         binance_sell.get_response()
                         ]

        time.sleep(1)

        status_list = [coinbase_buy.get_status(full=True),
                       coinbase_sell.get_status(full=True),
                       binance_buy.get_status(full=True),
                       binance_sell.get_status(full=True)
                       ]

        self.assertTrue(compare_responses(response_list))

        self.assertTrue(compare_responses(status_list))

    def check_limit_order(self, limit_order: LimitOrder, expected_side: str, size, product_id):
        self.assertEqual(limit_order.get_side(), expected_side)
        self.assertEqual(limit_order.get_type(), 'limit')
        self.assertEqual(limit_order.get_time_in_force(), 'GTC')
        # TODO fix status homogeneity
        # self.assertEqual(limit_order.get_status(), {'status': 'new'})
        self.assertEqual(limit_order.get_quantity(), size)
        self.assertEqual(limit_order.get_asset_id(), product_id)

    def test_limit_order(self):
        """
        This function tests a few components of market orders:
        - Opening market orders
        - Monitoring market orders using the order status function
        - Comparing with open orders
        - Canceling orders
        """
        binance_limits = self.Binance_Interface.get_asset_limits('BTC-USDT')

        binance_buy = self.Binance_Interface.limit_order('BTC-USDT', 'buy', int(binance_limits['min_price']+30), .01)
        time.sleep(3)
        self.check_limit_order(binance_buy, 'buy', .01, 'BTC-USDT')

        coinbase_buy = self.Coinbase_Pro_Interface.limit_order('BTC-USD', 'buy', .01, .001)
        self.check_limit_order(coinbase_buy, 'buy', .001, 'BTC-USD')

        binance_sell = self.Binance_Interface.limit_order('BTC-USDT', 'sell', int(binance_limits['max_price']-30), .01)
        self.check_limit_order(binance_sell, 'sell', .01, 'BTC-USDT')

        coinbase_sell = self.Coinbase_Pro_Interface.limit_order('BTC-USD', 'sell', 100000, .001)
        self.check_limit_order(coinbase_sell, 'sell', .001, 'BTC-USD')

        limits = [binance_buy, coinbase_buy, binance_sell, coinbase_sell]
        responses = []
        status = []

        cancels = []

        coinbase_open = self.Coinbase_Pro_Interface.get_open_orders('BTC-USD')
        for i in [coinbase_buy, coinbase_sell]:
            found = False
            for j in coinbase_open:
                if i.get_id() == j['id']:
                    found = True
            self.assertTrue(found)

        binance_open = self.Binance_Interface.get_open_orders('BTC-USDT')
        for i in [binance_buy, binance_sell]:
            found = False
            for j in binance_open:
                if i.get_id() == j['id']:
                    found = True
                    compare_dictionaries(i.get_response(), j)
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

        self.assertTrue(compare_responses(cancels, force_exchange_specific=False))

    def test_get_keys(self):
        responses = []
        for i in self.interfaces:
            responses.append(i.get_fees())

        self.assertTrue(compare_responses(responses))

    def test_get_product_history(self):
        # Setting for number of hours to test backwards to
        test_intervals = 100

        current_time = time.time()
        intervals_ago = time.time() - (build_hour() * test_intervals)

        responses = []
        for i in self.interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.get_product_history('BTC-USDT', intervals_ago, current_time, 3600))
            else:
                responses.append(i.get_product_history('BTC-USD', intervals_ago, current_time, 3600))

        print(responses)

        for i in responses:
            self.assertTrue(isinstance(i['time'], pd.Series))
            self.assertTrue(isinstance(i['low'], pd.Series))
            self.assertTrue(isinstance(i['high'], pd.Series))
            self.assertTrue(isinstance(i['open'], pd.Series))
            self.assertTrue(isinstance(i['close'], pd.Series))
            self.assertTrue(isinstance(i['volume'], pd.Series))

            self.assertTrue(len(i) == test_intervals)

            self.assertTrue(isinstance(i['time'][0], numpy.int64))
            self.assertTrue(isinstance(i['low'][0], float))
            self.assertTrue(isinstance(i['high'][0], float))
            self.assertTrue(isinstance(i['open'][0], float))
            self.assertTrue(isinstance(i['close'][0], float))
            self.assertTrue(isinstance(i['volume'][0], float))

    def test_get_asset_limits(self):
        responses = []

        for i in self.interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.get_asset_limits('BTC-USDT'))
            else:
                responses.append(i.get_asset_limits('BTC-USD'))

        self.assertTrue(compare_responses(responses))

    def get_price(self):
        responses = []

        for i in self.interfaces:
            if i.get_exchange_type() == "binance":
                responses.append(i.get_price('BTC-USDT'))
            else:
                responses.append(i.get_price('BTC-USD'))

        for i in responses:
            self.assertTrue(isinstance(i, float))
