# Object for managing information about the exchange
import Coinbase_Pro.Coinbase_Pro, Exchange as Exchange
# The API itself
from Coinbase_Pro.Coinbase_Pro_API import API as Coinbase_Pro_API
from Coinbase_Pro.Coinbase_Pro_Tickers import Tickers as Coinbase_Pro_Ticker

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
            if id == None:
                return self.__calls.getPortfolio()
            else:
                return self.__calls.getPortfolio("id")

    """
    Used for buying or selling market orders
    """
    def market_order(self, size, side, id):
        if self.__type == "coinbase_pro":
            order = Coinbase_Pro_Utils.CoinbaseProUtils().generate_market_order(size, side, id)
            # TODO exchange object needs to be generated here and then returned at some point, this invovles creating a ticker. Tickers are something that need to be managed carefully
            self.__calls.placeOrder(order)

    """
    Used for buying or selling limit orders
    """
    def limit_order(self, size, price, side, id):
        if self.__type == "coinbase_pro":
            order = Coinbase_Pro_Utils.CoinbaseProUtils().generate_limit_order(size, price, side, id)
            # TODO exchange object needs to be generated here and then returned at some point, this invovles creating a ticker. Tickers are something that need to be managed carefully
            self.__calls.placeOrder(order)

    """
    Creates ticker connection.
    """
    def create_ticker(self, callback, currency_id, log=""):
        if self.__type == "coinbase_pro":
            ticker = Coinbase_Pro_Ticker(currency_id, log=log)
            ticker.append_callback(callback)
            return ticker