import time

import pandas as pd

import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder


class OkexInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 300, 900, 3600, 21600, 86400])

    def init_exchange(self):
        # This is purely an authentication check which can be disabled in settings
        fees = self.calls.get_trade_fee()
        try:
            if fees['message'] == "Invalid API Key":
                raise LookupError("Invalid API Key. Please check if the keys were input correctly into your "
                                  "keys.json.")
        except KeyError:
            pass

    def get_products(self):
        needed = self.needed['get_products']

        products = self.calls.get_coin_info()
        for i in range(len(products)):
            # Rename needed
            products[i]["symbol"] = products[i].pop("instrument_id")
            products[i]["base_asset"] = products[i].pop("base_currency")
            products[i]["quote_asset"] = products[i].pop("quote_currency")
            products[i]["base_min_size"] = products[i].pop("min_size")
            #products[i]["base_max_size"] = products[i].pop("min_size")
            products[i]["base_increment"] = products[i].pop("size_increment")
            products[i] = utils.isolate_specific(needed, products[i])
        return products

    def get_account(self, symbol=None) -> utils.AttributeDict:

        symbol = super().get_account(symbol=symbol)

        needed = self.needed['get_account']

        """
        [
            {
                "frozen":"0",
                "hold":"0",
                "id": "",
                "currency":"BTC",
                "balance":"0.0049925",
                "available":"0.0049925",
                "holds":"0"
            },
        """

        accounts = self.calls.get_account_info()
        parsed_dictionary = utils.AttributeDict({})
        # We have to sort through it if the accounts are none
        if symbol is not None:
            for i in accounts:
                if i["currency"] == symbol:
                    parsed_value = utils.isolate_specific(needed, i)
                    dictionary = utils.AttributeDict({
                        'available': parsed_value['available'],
                        'hold': parsed_value['holds']
                    })
                    return dictionary
            raise ValueError("Symbol not found")
        for i in range(len(accounts)):
            parsed_dictionary[accounts[i]['currency']] = utils.AttributeDict({
                'available': float(accounts[i]['available']),
                'hold': float(accounts[i]['holds'])
            })

        return parsed_dictionary

    @utils.order_protection
    def market_order(self, symbol, side, size) -> MarketOrder:
        needed = self.needed['market_order']
        """
            {
                "result": "true",
                "request_id": "",
                "client_oid": "b1234",
                "order_id": "131801215763791872",
                "error_message": "",
                "error_code": "0"
            }
        """
        order = {
            'symbol': symbol,
            'size': size,
            'side': side,
            'type': 'market'
        }

        response = self.calls.take_order(symbol, side, size=size)
        if "message" in response:
            raise InvalidOrder("Invalid Order: " + response["message"])
        response["created_at"] = time.time()
        response["id"] = response.pop('order_id')
        response["status"] = response.pop('result')
        response["symbol"] = symbol
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    # limit-order

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        Returns:
            dict: Containing the order_id of cancelled order. Example::
            { "client_oid": "order123", }
        """
        return {"order_id": self.calls.revoke_order(symbol)}

    def get_open_orders(self, symbol: str) -> list:
        """
        List open orders
        """
        """
        [
            {
                "client_oid":"oktspot86",
                "created_at":"2019-03-20T03:28:14.000Z",
                "filled_notional":"0",
                "filled_size":"0",
                "funds":"",
                "instrument_id":"BTC-USDT",
                "notional":"",
                "order_id":"2511109744100352",
                "order_type":"0",
                "price":"3594.7",
                "price_avg":"",
                "product_id":"BTC-USDT",
                "side":"buy",
                "size":"0.001",
                "status":"open",
                "fee_currency":"BTC",
                "fee":"-0.01",
                "rebate_currency":"open",
                "rebate":"0.05",
                "state":"0",
                "timestamp":"2019-03-20T03:28:14.000Z",
                "type":"limit"
            }
        ]
        """
        if symbol is None:
            raise ValueError()
        else:
            orders = list(self.calls.get_orders_list(instrument_id=symbol))

        if len(orders) == 0:
            return []
        if orders[0] == 'message':
            raise InvalidOrder("Invalid Order: " + str(orders))

        for i in range(len(orders)):
            orders[i]["created_at"] = utils.epoch_from_iso8601(orders[i]["timestamp"])
            needed = self.choose_order_specificity(orders[i]['type'])
            orders[i]["symbol"] = orders[i].pop('instrument_id')
            orders[i]["id"] = orders[i].pop('order_id')
            orders[i]["status"] = orders[i].pop('state')
            orders[i]["time_in_force"] = None
            orders[i] = utils.isolate_specific(needed, orders[i])

        return orders

    def get_order(self, symbol, order_id) -> dict:
        response = self.calls.get_order_info(order_id=order_id)

        if 'message' in response:
            raise APIException("Invalid: " + str(response['message']) + ", was the order canceled?")

        response["created_at"] = utils.epoch_from_iso8601(response["timestamp"])

        if response['type'] == 'market':
            needed = self.needed['market_order']
        elif response['type'] == 'limit':
            needed = self.needed['limit_order']
        else:
            needed = self.needed['market_order']

        response["symbol"] = response.pop('instrument_id')
        response["id"] = response.pop('order_id')
        response["status"] = response.pop('state')
        response["time_in_force"] = None
        return utils.isolate_specific(needed, response)

    def get_fees(self) -> dict:
        needed = self.needed['get_fees']
        """
        {
            "category": "1",
            "maker": "0.0002",
            "taker": "0.0005",
            "timestamp": "2019-12-11T11:02:31.360Z"
        }
        """
        fees = self.calls.get_trade_fee()
        fees['taker_fee_rate'] = fees.pop('taker')
        fees['maker_fee_rate'] = fees.pop('maker')
        return utils.isolate_specific(needed, fees)

    #def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):

    def get_order_filter(self, symbol: str) -> dict:
        response = self.calls.get_coin_info()
        products = None
        for i in response:
            if i["id"] == symbol:
                products = i
                break

        base_min_size = float(products.pop('min_size'))
        # base_max_size = float(products.pop('base_max_size'))
        base_increment = float(products.pop('size_increment'))

        return {
            "symbol": products.pop('instrument_id'),
            "base_asset": products.pop('base_currency'),
            "quote_asset": products.pop('quote_currency'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": base_min_size,  # Minimum size to buy
                # "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": base_increment,  # Specifies the minimum increment
                # for the base_asset.
                "price_increment": float(products['tick_size']),

                "min_price": float(products['tick_size']),
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,

                "base_min_size": base_min_size,  # Minimum size to buy
                #"base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": base_increment,  # Specifies the minimum increment

                "quote_increment": float(products.pop('tick_size')),  # Specifies the min order price as well
                # as the price increment.
                "buy": {
                    #"min_funds": float(products['min_market_funds']),
                    #"max_funds": float(products['max_market_funds']),
                },
                "sell": {
                    #"min_funds": float(products.pop('min_market_funds')),
                    #"max_funds": float(products.pop('max_market_funds')),
                },
            },
            "exchange_specific": {**products}
        }

    #def get_price(self, symbol) -> float:
