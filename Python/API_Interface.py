# Object for managing information about the exchange
import Coinbase_Pro.Coinbase_Pro, Exchange as Exchange
# The API itself
from Coinbase_Pro.Coinbase_Pro_API import API as Coinbase_Pro_API

import Coinbase_Pro.Coinbase_Pro_Utils as Coinbase_Pro_Utils

class APIInterface:
    def __init__(self, type, authenticated_API):
        self.__type = type
        self.__calls = authenticated_API

    """
    Get all currencies in an account
    """
    def get_currencies(self, id=None):
        if self.__type == "coinbase_pro":
            assert isinstance(self.__calls, Coinbase_Pro_API)
            if id == None:
                return self.__calls.getAccounts()
            else:
                return self.__calls.getAccounts("id")

    """
    Used for buying or selling market orders
    """
    def market_order(self, size, side, id):
        if self.__type == "coinbase_pro":
            assert isinstance(self.__calls, Coinbase_Pro_API)
            order = Coinbase_Pro_Utils.CoinbaseProUtils().generate_market_order(size, side, id)
            # TODO exchange object needs to be generated here and then returned at some point, this invovles creating a ticker. Tickers are something that need to be managed carefully
            self.__calls.placeOrder(order)
            return Exchange.Exchange(order,TICKERRRR)