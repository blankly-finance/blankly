"""
    Unit tests for Binance.
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


class BinanceInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Binance = Blankly.Binance(portfolio_name="Spot Test Key")
        cls.Binance_Interface = cls.Binance.get_interface()

    def test_get_exchange_type(self):
        binance = self.Binance_Interface.get_exchange_type()
        self.assertEqual(binance, "binance")
