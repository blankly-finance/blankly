"""
    Unit tests for Coinbase Pro.
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
import unittest


class CoinbaseInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Coinbase_Pro = Blankly.Coinbase_Pro(portfolio_name="Sandbox Portfolio",
                                                keys_path='./tests/config/keys.json',
                                                settings_path="./tests/config/settings.json")
        cls.Coinbase_Pro_Interface = cls.Coinbase_Pro.get_interface()

    def test_get_exchange_type(self):
        coinbase_pro = self.Coinbase_Pro_Interface.get_exchange_type()
        self.assertEqual(coinbase_pro, "coinbase_pro")

    # def test_market_order(self):
    #     cbp_status = self.Coinbase_Pro_Interface.get_paper_trading_status()
    #
    #     self.assertTrue(cbp_status)
