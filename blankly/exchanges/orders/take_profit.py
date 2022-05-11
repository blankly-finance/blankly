"""
    Class to manage a limit order lifecycle - a way to determine individual information about each buy and sell
    Copyright (C) 2022 Matias Kotlik, Emerson Dove

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


class TakeProfitOrder(Order):
    """
    (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value),
    limit if there is one)
    """

    def __init__(self, order, response, interface):
        self.Interface = interface
        self.__exchange = self.Interface.get_exchange_type()
        self.__order = order
        self.__response = response
        self.__homogenized_result = None
        super().__init__(self.__response, self.__order, self.Interface)

    def get_price(self) -> float:
        """
        Get the price that the order was set at. For limits this will be user-specified, for markets this will
        be market price.
        """
        return self.__response["price"]

    def get_time_in_force(self) -> str:
        """
        Get the exchange's set time_in_force value.
        """
        return self.__response["time_in_force"]

    def __str__(self):
        return_string = super().__str__()

        return_string = self.add_new_line(return_string, "Take Profit Order Parameters: ")

        return_string = self.add_new_line(return_string, "Time In Force: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_time_in_force())

        return_string = self.add_new_line(return_string, "Price: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_price())

        return return_string

    # override this here to homogenize these strings
    def get_type(self) -> str:
        return 'take_profit'
