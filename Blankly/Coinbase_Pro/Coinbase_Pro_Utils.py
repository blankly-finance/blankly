"""
    Utils for creating objects related to interacting with Coinbase Pro.
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


class CoinbaseProUtils:
    def __init__(self):
        pass


    """
    Size: Amount of base currency to buy or sell
    Price: Price per bitcoin
    Ex: Buy .001BTC at $15,000 is generateLimitOrder(.001, 15000, "buy", "BTC-USD")
    """
    """
    Order Place Example:
    order = {
        'size': 1.0,
        'price': 1.0,
        'side': 'buy',
        'product_id': 'BTC-USD',
    }
    (size in currency (like .01 BTC), buy/sell (string), product id (BTC-USD))
    """
    def generate_limit_order(self, size, price, side, product_id):
        order = {
            'size': size,
            'price': price,
            'side': side,
            'product_id': product_id,
        }
        return order
