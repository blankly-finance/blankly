"""
    Inherited class to abstract the similarities between order types
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
from blankly.utils.utils import pretty_print_JSON


class Order:
    def __init__(self, response, order, interface):
        """
        Limit Order:
        needed = [
            ["symbol", str],    <- similar
            ["id", str],    <- similar
            ["created_at", float],  <- similar
            ["price", float],
            ["size", float],
            ["status", str],    <- similar
            ["time_in_force", str],     <-similar
            ["type", str],  <- similar
            ["side", str]   <- similar
        ]

        Market Order:
        needed = [
            ["symbol", str],
            ["id", str],
            ["created_at", float],
            ["funds", float],
            ["status", str],
            ["type", str],
            ["side", str]
        ]
        """
        self.__response = response
        self.__order = order
        self.Interface = interface

    @staticmethod
    def add_new_line(input_string, *components, newline=True):
        for i in components:
            input_string += str(i)
        if newline:
            input_string += "\n"
        return input_string

    def __str__(self):
        return_string = ""
        return_string = self.add_new_line(return_string, "General Order Parameters: ")

        return_string = self.add_new_line(return_string, "Response: ")
        return_string = self.add_new_line(return_string, pretty_print_JSON(self.get_response(), actually_print=False))

        return_string = self.add_new_line(return_string, "Full Status: ")
        return_string = self.add_new_line(return_string, pretty_print_JSON(self.get_status(full=True),
                                                                           actually_print=False))

        return_string = self.add_new_line(return_string, "ID: ", self.get_id())

        return_string = self.add_new_line(return_string, "Symbol: ", self.get_asset_id())

        return_string = self.add_new_line(return_string, "Purchase Time: ", self.get_purchase_time())

        return_string = self.add_new_line(return_string, "Type: ", self.get_type())

        return_string = self.add_new_line(return_string, "Side: ", self.get_side())

        return_string = self.add_new_line(return_string, "Size: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_size())

        return return_string

    def get_response(self) -> dict:
        """
        Get the original but parsed response from the exchange.
        """
        return self.__response

    def get_id(self) -> str:
        """
        Get the exchange-set order ID.
        """
        return self.__response["id"]

    def get_asset_id(self) -> str:
        """
        Get the asset id of the exchange
        """
        return self.__response["symbol"]

    def get_purchase_time(self) -> float:
        """
        Get when the purchase was created at. This may be set at slightly different points within an
        exchange's matching engine.
        """
        return self.__response["created_at"]

    def get_status(self, full=False) -> dict:
        """
        Calls the exchange with the order id of this purchase and returns the homogenized output
        Args:
            full: Set this to True to receive the all the order details. Default is False, which returns just the status
            field as (example) {"status:" "NEW"}
        """
        if full:
            return self.Interface.get_order(self.__order["symbol"], self.get_id())
        else:
            return {"status": self.Interface.get_order(self.__order["symbol"], self.get_id())["status"]}

    def get_type(self) -> str:
        """
        Get order type, such as market/limit/stop.
        """
        return self.__response["type"]

    def get_side(self) -> str:
        """
        Get the order side such as buy/sell as a str.
        """
        return self.__response["side"]

    def get_size(self) -> float:
        """
        Get the size of order, Ex: .004 bitcoin
        """
        return self.__response["size"]
