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
import unittest
import time

from Blankly.utils.purchases.market_order import MarketOrder


def compare_responses(response_list):
    """
    Compare a set of responses against the others. This supports a large set of interfaces
    """
    for i in range(len(response_list)-1):
        if not compare_dictionaries(response_list[i], response_list[i+1]):
            print("Failed checking index " + str(i+1) + " against index " + str(i))
            return False
    return True


class InterfaceHomogeneity(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.Interfaces = []

        cls.Coinbase_Pro = Blankly.Coinbase_Pro(portfolio_name="Sandbox Portfolio")
        cls.Coinbase_Pro_Interface = cls.Coinbase_Pro.get_interface()
        cls.Interfaces.append(cls.Coinbase_Pro_Interface)

        cls.Binance = Blankly.Binance(portfolio_name="Spot Test Key")
        cls.Binance_Interface = cls.Binance.get_interface()
        cls.Interfaces.append(cls.Binance_Interface)

        cls.Paper_Trade = Blankly.PaperTrade(cls.Binance.get_interface())
        cls.Paper_Trade_Interface = cls.Paper_Trade.get_interface()
        cls.Interfaces.append(cls.Paper_Trade_Interface)

    def test_get_products(self):
        responses = []
        for i in range(len(self.Interfaces)):
            responses[i] = self.Interfaces[i].get_products()[0]

        self.assertTrue(responses)

    def test_get_account(self):
        responses = []
        for i in range(len(self.Interfaces)):
            responses[i] = self.Interfaces[i].get_account()[0]

        self.assertTrue(responses)

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

        self.assertLess(order1.get_purchase_time(), time.time())
        self.assertEqual(order1.get_time_in_force(), "GTC")

    def test_market_order(self):
        binance_status = self.Binance_Interface.get_paper_trading_status()
        # coinbase_pro_status = self.Binance_Interface.get_paper_trading_status()

        self.assertTrue(binance_status)
        # self.assertTrue(coinbase_pro_status)

        # Make sure to buy back the funds we're loosing from fees - minimum balance of .1 bitcoin
        btc_account = self.Binance_Interface.get_account(currency="BTCT")['available']
        if btc_account < .1:
            price = self.Binance_Interface.get_price("BTC-USDT")
            self.Binance_Interface.market_order("BTC-USDT", "buy", price * .1)

        binance_buy = self.Binance_Interface.market_order('BTC-USDT', 'buy', 20)
        binance_sell = self.Binance_Interface.market_order('BTC-USDT', 'sell', 20)

        self.assertTrue(self.check_market_order(binance_buy, 'buy', 20))
        self.assertTrue(self.check_market_order(binance_sell, 'sell', 20))

        self.assertTrue(compare_dictionaries(binance_buy.get_response(), binance_sell.get_response()))
        self.assertTrue(compare_dictionaries(binance_buy.get_status(full=True), binance_sell.get_status(full=True)))
