import Constants, time, LocalAccount
from Utils import Utils
""" Class to manage exchange lifecycle - API calls are routed through here """
class Exchange:
    """ (Buying or selling (string), amount in currency (BTC/XLM), ticker object (so we can get time and value), limit if there is one) """
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
            # These have to include fees on buy/sell because someone has to calculate them
            self.__utils.tradeLocal(order["side"], self.__ticker.getCoinID(), order["size"], self.getAmountCurrencyExchanged(), self.__ticker)
        else:
            response = self.__calls.placeOrder()
            self.__coinBaseId = response["id"]

    def getPurchaseTime(self):
        return self.__purchaseTime

    def getSetLimit(self):
        return self.__limit

    """
    When these orders are used the amount of currency changes throughout the lifetime by the fee rate each time
    """
    def getAmountCurrencyExchanged(self):
        return self.__amountCurrency - (self.__amountCurrency * Constants.PRETEND_FEE_RATE)

    def getAmountCurrencyOnSell(self):
        return self.getAmountCurrencyExchanged() - (self.getAmountCurrencyExchanged() * Constants.PRETEND_FEE_RATE)

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
                    print True
                return True
            else:
                if show:
                    print False
                return False
        else:
            if self.getProfitableSellPrice() > float(self.__ticker.getMostRecentTick()["price"]):
                if show:
                    print True
                return True
            else:
                if show:
                    print False
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
            print fee
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
            print "Cannot cancel order"

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
        price = self.__valueAtTime/(1 - (2 * Constants.PRETEND_FEE_RATE) + (Constants.PRETEND_FEE_RATE * Constants.PRETEND_FEE_RATE))
        if show:
            print price
        return price

    """ This allows this to be checked if this buy became profitable """
    def inProfitableSellZone(self, show=False):
        self.__profitable = float((self.__ticker.getMostRecentTick()["price"])) > self.getProfitableSellPrice()
        if show:
            print self.__profitable
        return self.__profitable

    """ Allows this exchange to be sold back in its entirety """
    def sellSelf(self):
        if self.__calls is not None:
            # This doesn't need the fee calculation because that happens anyway
            self.__calls.placeOrder(self.__utils.generateMarketOrder(self.getAmountCurrencyExchanged(), "sell", self.__ticker.getCoinID()))
        else:
            print("Selling locally only")
            # This one needs to include fees before and after
            self.__utils.tradeLocal("sell", self.__ticker.getCoinID(), self.getAmountCurrencyExchanged(), self.getAmountCurrencyOnSell(), self.__ticker)
        self.__sold = True


    def setIfPastSellMin(self, val):
        self.__reachedPastMinToSell = val

    def getIfPastSellMin(self, show=False):
        if show:
            print self.__reachedPastMinToSell
        return self.__reachedPastMinToSell

    def getIfSold(self):
        return self.__sold