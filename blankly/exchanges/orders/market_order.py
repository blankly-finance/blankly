"""
    Class to manage a market order lifecycle - a way to determine individual information about each buy and sell
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


class MarketOrder(Order):
    """
    (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value),
    limit if there is one)
    """

    def __init__(self, order, response, interface):
        """
        Coinbase Response:
        {
            'id': '5955cd5d-a78c-4c47-9741-1f7f20ac7f95',
            'product_id': 'BTC-USD',
            'side': 'buy',
            'stp': 'dc',
            'funds': '10.97804391',
            'specified_funds': '11',
            'type': 'market',
            'post_only': False,
            'created_at': 1621039946.320796,
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

    def __str__(self):
        return_string = super().__str__()

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
