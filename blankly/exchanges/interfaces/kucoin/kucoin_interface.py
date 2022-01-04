import time

import pandas as pd

import blankly.utils.time_builder
import blankly.utils.utils as utils
import kucoin
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder

class KucoinInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 300, 900, 3600, 21600, 86400])

    def init_exchange(self):

        fees = self.calls.get_fees()
        try:
            if fees['message'] == "Invalid API Key":
                raise LookupError("Invalid API Key - are you trying to use your normal exchange keys "
                                  "while in sandbox mode? \nTry toggling the \'use_sandbox\' setting "
                                  "in your settings.json or check if the keys were input correctly into your "
                                  "keys.json.")
        except KeyError:
            pass

    def get_products(self):
        needed = self.needed['get_products']
        """
        [
          {
            "symbol": "XLM-USDT",
            "name": "XLM-USDT",
            "baseCurrency": "XLM",
            "quoteCurrency": "USDT",
            "feeCurrency": "USDT",
            "market": "USDS",
            "baseMinSize": "0.1",
            "quoteMinSize": "0.01",
            "baseMaxSize": "10000000000",
            "quoteMaxSize": "99999999",
            "baseIncrement": "0.0001",
            "quoteIncrement": "0.000001",
            "priceIncrement": "0.000001",
            "priceLimitRate": "0.1",
            "isMarginEnabled": true,
            "enableTrading": true
          },
        ]
        """
        products = self.calls.kucoin.m
        for i in range(len(products)):
            products[i]["base_asset"] = products[i].pop("baseCurrency")
            products[i]["quote_asset"] = products[i].pop("quoteCurrency")
            products[i]["base_min_size"] = products[i].pop("baseMinSize")
            products[i]["base_max_size"] = products[i].pop("baseMaxSize")
            products[i]["base_increment"] = products[i].pop("baseIncrement")
            products[i] = utils.isolate_specific(needed, products[i])
        return products

    def get_account(self, symbol=None) -> utils.AttributeDict:
        """
            Get all currencies in an account, or sort by symbol/account_id
            Args:
                symbol (Optional): Filter by particular symbol

                These arguments are mutually exclusive
        """
        account_id = super().account()
        symbol = super().get_account(symbol=symbol)
        needed = self.needed['get_account']
        """
        {
            "currency": "KCS",  
            "balance": "1000000060.6299",  
            "available": "1000000060.6299",  
            "holds": "0" 
        }
        """

        account = self.calls.get_accounts()
    @utils.order_protection
    def market_order(self, symbol, side, size) -> MarketOrder:
        """
            Used for buying or selling market orders
            Args:
                symbol: currency to buy
                side: buy/sell
                size: desired amount of base currency to buy or sell
        """
        needed = self.needed['market_order']
        """
        {
            "orderId": "5bd6e9286d99522a52e458de"
        }
        """

        order = {
            'symbol': symbol,
            'size': size,
            'side': side,
            'type': 'market',
        }

        response = self.calls.place_market_order(symbol, side, size=size)
        #response_data = self.calls.
        if "message" in response:
            raise InvalidOrder("Invalid Order: " + response["message"])
        response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
        response["symbol"] = response.pop('product_id')
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    @utils.order_protection
    def limit_order(self, symbol, side, price, size) -> LimitOrder:
        """
            Used for buying or selling limit orders
            Args:
                symbol: currency to buy
                side: buy/sell
                price: price to set limit order
                size: amount of currency (like BTC) for the limit to be valued
        """
        needed = self.needed['limit_order']

        order = {
            'symbol': symbol,
            'size': size,
            'side': side,
            'price': price,
            'type': 'limit',
        }
        response = self.calls.place_limit_order(symbol, side, price, size=size)
        if "message" in response:
            raise InvalidOrder("Invalid Order: " + response["message"])
        response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
        response["symbol"] = response.pop('product_id')
        response = utils.isolate_specific(needed, response)
        return LimitOrder(order, response, self)