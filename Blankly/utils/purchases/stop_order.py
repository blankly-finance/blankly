"""
    Class to manage a stop order lifecycle - a way to determine individual information about each buy and sell
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
from Blankly.utils.purchases.order import Order


class MarketOrder(Order):
    """
    (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value),
    limit if there is one)
    """

    def __init__(self, order, response, interface):
        """
        Coinbase Response:
        {
            'id': '3a98a5c6-05a0-4e46-b8e4-3f27358fe27d',
            'price': '29500',
            'size': '0.01',
            'product_id':
            'BTC-USD',
            'side': 'buy',
            'stp': 'dc',
            'type': 'limit',
            'time_in_force':
            'GTC',
            'post_only': False,
            'created_at': '2021-05-28T19:24:52.010449Z',
            'stop': 'loss',
            'stop_price': '30000',
            'fill_fees': '0',
            'filled_size': '0',
            'executed_value': '0',
            'status': 'pending',
            'settled': False
        }
        Binance Response:
        TODO add this

        Guaranteed:
        needed = [
            ["product_id", str],
            ["id", str],
            ["created_at", float],
            ["funds", float],
            ["status", str],
            ["type", str],
            ["side", str]
        ]
        """
        self.Interface = interface
        self.__exchange = self.Interface.get_exchange_type()
        self.__order = order
        self.__response = response
        self.__homogenized_result = None
        super().__init__(self.__response, self.__order, self.Interface)

    def get_funds(self) -> float:
        """
        Get the funds exchanged in a market order. This will include fees.
        """
        return self.__response["funds"]
