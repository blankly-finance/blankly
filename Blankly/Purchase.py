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

import Blankly.utils
import Blankly.Constants


class Purchase:
    """ (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value),
    limit if there is one) """

    def __init__(self, order, response, ticker, exchange_properties):
        self.__buyOrSell = order["side"]
        self.__purchaseTime = (ticker.get_most_recent_tick())["time"]
        # Assigned below if there is an ApiCall attached
        self.__purchase_id = None
        self.__response = response
        self.__exchange_properties = exchange_properties

        try:
            self.__limit = order["price"]
        except Exception as e:
            self.__limit = None

        self.__valueAtTime = float((ticker.get_most_recent_tick())["price"])
        # This is the amount before fees
        self.__amountCurrency = order["size"]
        self.__ticker = ticker
        """ 
        self.__profitable is for any degree of profitability
        self.__reachedPastSellMin is if it's gone up a significant amount
        """
        self.__profitable = False
        self.__reachedPastMinToSell = False
        self.__sold = False

    def get_purchase_time(self):
        return self.__purchaseTime

    def get_set_limit(self):
        return self.__limit

    """
    When these orders are used the amount of currency changes throughout the lifetime by the fee rate each time
    """
    def get_amount_currency_exchanged(self):
        return self.__amountCurrency
    """
    On sell, we want to know how much money we got back.
    """
    def get_value_returned_on_sell(self):
        # TODO
        return None

    def get_side(self):
        return self.__buyOrSell

    def get_value_at_time(self):
        return self.__valueAtTime

    def get_purchase_id(self):
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

        # Old algorithm that didn't take into account the change in amount actually bought because of the fee
        # print("Before fees: " + str((self.__valueAtTime * self.__amountCurrency)))
        # then = (self.__valueAtTime * self.__amountCurrency)
        # now = (float((self.__ticker.getMostRecentTick())["price"]) * self.__amountCurrency)
        # if show:
        #     print("Before fees now: " + str(now))
        #     print("Before fees then: " + str(then))
        #     print("Difference with fees: " + str(((now - (now * Constants.PRETEND_FEE_RATE)) - (then - (then * Constants.PRETEND_FEE_RATE)))))
        #
        # if self.__buyOrSell == "buy":
        #     if ((now - (now * Constants.PRETEND_FEE_RATE)) - (then - (then * Constants.PRETEND_FEE_RATE))) > 0:
        #         return True
        #     else:
        #         return False
        # else:
        #     if ((then - (then * Constants.PRETEND_FEE_RATE)) - (now - (now * Constants.PRETEND_FEE_RATE))) > 0:
        #         return True
        #     else:
        #         return False

    def get_fee(self, show=False):
        fee = (self.__valueAtTime * self.__amountCurrency) * Blankly.Constants.PRETEND_FEE_RATE
        if show:
            print(fee)
        return fee

    # def cancel_order(self):
    #     if self.__calls is not None:
    #         response = self.__calls.deleteOrder(self.__purchase_id, show=False)
    #         try:
    #             if response["message"] == "Unauthorized.":
    #                 print("Not authorized to delete order: " + self.__purchase_id)
    #         except TypeError as e:
    #             print("Canceled Order " + response)
    #         except Exception as e:
    #             print("FAILED to cancel order " + self.__purchase_id)
    #         self.__active = False
    #     else:
    #         print("Cannot cancel order")

    # def confirm_canceled(self):
    #     if self.__calls is not None:
    #         response = self.__calls.getOpenOrders()
    #         for i in range(len(response)):
    #             if (response[i]["id"] == self.__purchase_id):
    #                 return False
    #         self.__active = False
    #         return True
    #     else:
    #         return "Cannot confirm cancellation"

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

    """ 
    Allows this exchange to be sold back in its entirety 
    """
    # # TODO - This has turned into spaghetti code, fix it
    # def sellSelf(self):
    #     if self.__calls is not None:
    #         # This doesn't need the fee calculation because that happens anyway
    #         self.__calls.placeOrder(
    #             self.__utils.generateMarketOrder(self.__amountCurrency, "sell", self.__ticker.get_currency_id()))
    #         Trade_Local.tradeLocal("sell", self.__ticker.get_currency_id(), self.__amountCurrency, self.__ticker)
    #     else:
    #         print("Selling locally only")
    #         # This one needs to include fees before and after
    #         self.__utils.tradeLocal("sell", self.__ticker.get_currency_id(), self.__amountCurrency, self.__ticker)
    #     self.__sold = True

    # def setIfPastSellMin(self, val):
    #     self.__reachedPastMinToSell = val
    #
    # def getIfPastSellMin(self, show=False):
    #     if show:
    #         print(self.__reachedPastMinToSell)
    #     return self.__reachedPastMinToSell

    # def getIfSold(self):
    #     return self.__sold
