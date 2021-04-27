"""
    Class to manage a purchase lifecycle - a way to determine individual information about each buy and sell
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

import Blankly.utils.utils
import Blankly.Constants


class Purchase:
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

        Binance Response:
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
        """
        self.Interface = interface
        self.__exchange = self.Interface.__exchange_name
        self.__side = order["side"]
        # Assigned below if there is an ApiCall attached
        self.__response = response

        try:
            self.__limit = order["price"]
        except Exception as e:
            self.__limit = None

    def get_purchase_time(self):
        return self.__purchaseTime

    """
    When these orders are used the amount of currency changes throughout the lifetime by the fee rate each time
    """
    def get_amount_currency_exchanged(self):
        return self.__amountCurrency

    def get_side(self):
        return self.__buyOrSell

    def get_id(self):
        return self.__purchase_id

    """ Returns true if the buy order can be sold at a profit or the sell order didn't loose money """
    def is_profitable(self, show=False):
        if self.__buyOrSell == "buy":
            if self.is_profitable_buy() < float(self.__ticker.get_most_recent_tick()["price"]):
                if show:
                    print(True)
                return True
            else:
                if show:
                    print(False)
                return False
        else:
            if self.is_profitable_buy() > float(self.__ticker.get_most_recent_tick()["price"]):
                if show:
                    print(True)
                return True
            else:
                if show:
                    print(False)
                return False

    def get_fee(self, show=False):
        fee = (self.__valueAtTime * self.__amountCurrency) * Blankly.Constants.PRETEND_FEE_RATE
        if show:
            print(fee)
        return fee

    """ 
    Returns the price that a BUY needs to reach to be profitable
    Ths can be used to set limit orders
    """
    def is_profitable_buy(self, show=False):
        # price = self.__valueAtTime/(1 - Constants.PRETEND_FEE_RATE)
        # This one didn't work for the USD amount modified
        # price = self.__valueAtTime/(1 - (2 * Constants.PRETEND_FEE_RATE) + (Constants.PRETEND_FEE_RATE * Constants.PRETEND_FEE_RATE))
        maker_fee_rate = self.__exchange_properties['maker_fee_rate']
        price = ((maker_fee_rate + 1) * (self.__valueAtTime) / (1 - maker_fee_rate))
        if show:
            print(price)
        return price

    """ 
    This allows this to be checked if this buy became profitable 
    """
    def is_profitable_sell(self, show=False):
        self.__profitable = float((self.__ticker.get_most_recent_tick()["price"])) > self.is_profitable_buy()
        if show:
            print(self.__profitable)
        return self.__profitable