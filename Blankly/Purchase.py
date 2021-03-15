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

import Constants, time, Local_Account.LocalAccount, Local_Account.Trade_Local as Trade_Local
from Utils import Utils
class Exchange:
    """ (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value),
    limit if there is one) """
    def __init__(self, order, coinTicker, ApiCalls=None):
        self.__buyOrSell = order["side"]
        self.__purchaseTime = (coinTicker.getMostRecentTick())["time"]
        # Assigned below if there is an ApiCall attached
        self.__coinBaseId = None
        self.__calls = ApiCalls

        try:
            self.__limit = order["price"]
        except Exception as e:
            self.__limit = None


        self.__valueAtTime = float((coinTicker.getMostRecentTick())["price"])
        # This is the amount before fees
        self.__amountCurrency = order["size"]
        self.__ticker = coinTicker
        self.__active = True
        self.__utils = Utils()
        """ 
        self.__profitable is for any degree of profitability
        self.__reachedPastSellMin is if it's gone up a significant amount
        """
        self.__profitable = False
        self.__reachedPastMinToSell = False
        self.__sold = False
        if self.__calls is None:
            print("Buying locally")
            # Fees are calculated in the tradelocal function
            Trade_Local.tradeLocal(order["side"], self.__ticker.getCoinID(), order["size"], self.__ticker)
        else:
            response = self.__calls.placeOrder(order, self.__ticker, show=False)
            self.__coinBaseId = response["id"]

    def getPurchaseTime(self):
        return self.__purchaseTime

    def getSetLimit(self):
        return self.__limit

    """
    When these orders are used the amount of currency changes throughout the lifetime by the fee rate each time
    """
    def getAmountCurrencyExchanged(self):
        return self.__amountCurrency

    """
    On sell, we want to know how many dollars we got back.
    """
    def getDollarReturnOnSell(self):
        # TODO
        return None

    def getBoughtOrSold(self):
        return self.__buyOrSell

    def getValueAtTime(self):
        return self.__valueAtTime

    def getCoinBaseId(self):
        return self.__coinBaseId

    def getIfActive(self):
        return self.__active

    """ Returns true if the buy order can be sold at a profit or the sell order didn't loose money """
    def isProfitable(self, show=False):
        if self.__buyOrSell == "buy":
            if self.getProfitableSellPrice() < float(self.__ticker.getMostRecentTick()["price"]):
                if show:
                    print (True)
                return True
            else:
                if show:
                    print (False)
                return False
        else:
            if self.getProfitableSellPrice() > float(self.__ticker.getMostRecentTick()["price"]):
                if show:
                    print (True)
                return True
            else:
                if show:
                    print (False)
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

    def getFee(self, show=False):
        fee = (self.__valueAtTime * self.__amountCurrency) * Constants.PRETEND_FEE_RATE
        if (show):
            print (fee)
        return fee

    def cancelOrder(self):
        if self.__calls is not None:
            response = self.__calls.deleteOrder(self.__coinBaseId, show=False)
            try:
                if response["message"] == "Unauthorized.":
                    print("Not authorized to delete order: " + self.__coinBaseId)
            except TypeError as e:
                print("Canceled Order " + response)
            except Exception as e:
                print("FAILED to cancel order " + self.__coinBaseId)
            self.__active = False
        else:
            print("Cannot cancel order")

    def confirmCanceled(self):
        if self.__calls is not None:
            response = self.__calls.getOpenOrders()
            for i in range(len(response)):
                if (response[i]["id"] == self.__coinBaseId):
                    return False
            self.__active = False
            return True
        else:
            return "Cannot confirm cancellation"

    """ 
    Returns the price that a BUY needs to reach to be profitable
    Ths can be used to set limit orders
    """
    def getProfitableSellPrice(self, show=False):
        # price = self.__valueAtTime/(1 - Constants.PRETEND_FEE_RATE)
        # This one didn't work for the USD amount modified
        # price = self.__valueAtTime/(1 - (2 * Constants.PRETEND_FEE_RATE) + (Constants.PRETEND_FEE_RATE * Constants.PRETEND_FEE_RATE))
        price = ((Constants.PRETEND_FEE_RATE + 1)*(self.__valueAtTime)/(1-Constants.PRETEND_FEE_RATE))
        if show:
            print(price)
        return price

    """ 
    This allows this to be checked if this buy became profitable 
    """
    def inProfitableSellZone(self, show=False):
        self.__profitable = float((self.__ticker.getMostRecentTick()["price"])) > self.getProfitableSellPrice()
        if show:
            print(self.__profitable)
        return self.__profitable

    """ 
    Allows this exchange to be sold back in its entirety 
    """
    # TODO - This has turned into spaghetti code, fix it
    def sellSelf(self):
        if self.__calls is not None:
            # This doesn't need the fee calculation because that happens anyway
            self.__calls.placeOrder(self.__utils.generateMarketOrder(self.__amountCurrency, "sell", self.__ticker.getCoinID()))
            Trade_Local.tradeLocal("sell", self.__ticker.getCoinID(), self.__amountCurrency, self.__ticker)
        else:
            print("Selling locally only")
            # This one needs to include fees before and after
            self.__utils.tradeLocal("sell", self.__ticker.getCoinID(), self.__amountCurrency, self.__ticker)
        self.__sold = True


    def setIfPastSellMin(self, val):
        self.__reachedPastMinToSell = val

    def getIfPastSellMin(self, show=False):
        if show:
            print(self.__reachedPastMinToSell)
        return self.__reachedPastMinToSell

    def getIfSold(self):
        return self.__sold