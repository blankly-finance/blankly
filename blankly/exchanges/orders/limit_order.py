"""
    Class to manage a limit order lifecycle - a way to determine individual information about each buy and sell
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


class LimitOrder(Order):
    """
    (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value),
    limit if there is one)
    """

    def __init__(self, order, response, interface):
        """
        Coinbase Response:
        {
            "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
            "price": "0.10000000",
            "size": "0.01000000",
            "product_id": "BTC-USD",
            "side": "buy",
            "stp": "dc",
            "type": "limit",
            "time_in_force": "GTC",
            "post_only": false,
            "created_at": "2016-12-08T20:02:28.53864Z",
            "fill_fees": "0.0000000000000000",
            "filled_size": "0.00000000",
            "executed_value": "0.0000000000000000",
            "status": "pending",
            "settled": false
        }

        binance Response:
        {
            "symbol": "BTCUSDT",
            "orderId": 28,
            "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
            "transactTime": 1507725176595,
            "price": "0.00000000",
            "origQty": "10.00000000",
            "executedQty": "10.00000000",
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": "SELL"
        }

        Guaranteed:
        needed = [
            ["symbol", str],
            ["id", str],
            ["created_at", float],
            ["price", float],
            ["size", float],
            ["status", str],
            ["time_in_force", str],
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

    def get_quantity(self) -> float:
        """
        Get the quantity of order, Ex: .004 bitcoin
        """
        return self.__response["size"]

    def __str__(self):
        return_string = super().__str__()

        return_string = self.add_new_line(return_string, "Limit Order Parameters: ")

        return_string = self.add_new_line(return_string, "Time In Force: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_time_in_force())

        return_string = self.add_new_line(return_string, "Price: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_price())

        return_string = self.add_new_line(return_string, "Quantity: ", newline=False)
        return_string = self.add_new_line(return_string, self.get_quantity())

        return return_string

    """ This is something that should be implemented in the future """
    # """ Returns true if the buy order can be sold at a profit or the sell order didn't loose money """
    # def is_profitable(self, show=False):
    #     if self.__buyOrSell == "buy":
    #         if self.is_profitable_buy() < float(self.__ticker.get_most_recent_tick()["price"]):
    #             if show:
    #                 print(True)
    #             return True
    #         else:
    #             if show:
    #                 print(False)
    #             return False
    #     else:
    #         if self.is_profitable_buy() > float(self.__ticker.get_most_recent_tick()["price"]):
    #             if show:
    #                 print(True)
    #             return True
    #         else:
    #             if show:
    #                 print(False)
    #             return False
    #
    # def get_fee(self, show=False):
    #     fee = (self.__valueAtTime * self.__amountCurrency) * blankly.Constants.PRETEND_FEE_RATE
    #     if show:
    #         print(fee)
    #     return fee
    #
    # """
    # Returns the price that a BUY needs to reach to be profitable
    # Ths can be used to set limit orders
    # """
    # def is_profitable_buy(self, show=False):
    #     # price = self.__valueAtTime/(1 - Constants.PRETEND_FEE_RATE)
    #     # This one didn't work for the USD amount modified
    #     # price = self.__valueAtTime/(1 - (2 * Constants.PRETEND_FEE_RATE) + (Constants.PRETEND_FEE_RATE * Constants.PRETEND_FEE_RATE))
    #     maker_fee_rate = self.__exchange_properties['maker_fee_rate']
    #     price = ((maker_fee_rate + 1) * (self.__valueAtTime) / (1 - maker_fee_rate))
    #     if show:
    #         print(price)
    #     return price
    #
    # """
    # This allows this to be checked if this buy became profitable
    # """
    # def is_profitable_sell(self, show=False):
    #     self.__profitable = float((self.__ticker.get_most_recent_tick()["price"])) > self.is_profitable_buy()
    #     if show:
    #         print(self.__profitable)
    #     return self.__profitable
