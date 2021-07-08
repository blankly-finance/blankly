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
from blankly.exchanges.orders.order import Order


class StopLimit(Order):
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
            'product_id': 'BTC-USD',
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
        binance Response:
        TODO add this

        Guaranteed:
        needed = [
                ["symbol", str],
                ["id", str],  <-- Handled by order
                ["created_at", float],  <-- Handled by order
                ["stop_price", float],
                ["limit_price", float],
                ["stop", str],
                ["size", float],
                ["status", str],  <-- Handled by order
                ["time_in_force", str],  <-- Handled by order
                ["type", str],  <-- Handled by order
                ["side", str]  <-- Handled by order
        ],
        """
        self.Interface = interface
        self.__exchange = self.Interface.get_exchange_type()
        self.__order = order
        self.__response = response
        self.__homogenized_result = None
        super().__init__(self.__response, self.__order, self.Interface)

    def get_stop_price(self) -> float:
        """
        Get the trigger price of the stop order
        """
        return self.__response["stop_price"]

    def get_limit_price(self) -> float:
        """
        Get the price that the limit is set at after triggering the stop
        """
        return self.__response["limit_price"]

    def get_stop_type(self) -> str:
        """
        Get if the stop type is "loss" or "entry"
        """
        return self.__response["stop"]

    def get_size(self) -> float:
        """
        Get the amount of base currency set in the triggered stop limit order
        """
        return self.__response["size"]

    def get_time_in_force(self) -> str:
        """
        Get the exchange's set time_in_force value.
        """
        return self.__response["time_in_force"]

    def __str__(self):
        return_string = super().__str__()

        return_string = self.add_new_line(return_string, "Stop Order Parameters: ")

        return_string = self.add_new_line(return_string, "Time In Force: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_time_in_force())

        return_string = self.add_new_line(return_string, "Stop Price: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_stop_price())

        return_string = self.add_new_line(return_string, "Stop Limit Price: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_limit_price())

        return_string = self.add_new_line(return_string, "Stop Type: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_stop_type())

        return_string = self.add_new_line(return_string, "Get Size: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_size())

        return return_string
