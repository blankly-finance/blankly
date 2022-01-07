import time

import pandas as pd
from kucoin import client as KucoinAPI

import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder


class KucoinInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 300, 900, 3600, 21600, 86400])
        self.calls: KucoinAPI = self.calls

    def init_exchange(self):
        assert isinstance(self.calls, KucoinAPI)
        fees = self.calls.User.get_base_fee()
        try:
            if fees['msg'] == "Invalid API Key":
                raise LookupError("Invalid API Key - are you trying to use your normal exchange keys "
                                  "while in sandbox mode? \nTry toggling the \'use_sandbox\' setting "
                                  "in your settings.json or check if the keys were input correctly into your "
                                   "keys.json.")
        except KeyError:
            pass

    def get_products(self):
        assert isinstance(self.calls, KucoinAPI)
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
        products = self.calls.Market.get_symbol_list()
        for i in range(len(products)):
            products[i]["base_asset"] = products[i].pop("baseCurrency")
            products[i]["quote_asset"] = products[i].pop("quoteCurrency")
            products[i]["base_min_size"] = products[i].pop("baseMinSize")
            products[i]["base_max_size"] = products[i].pop("baseMaxSize")
            products[i]["base_increment"] = products[i].pop("baseIncrement")
            products[i] = utils.isolate_specific(needed, products[i])
        return products

    # def get_account(self, symbol=None) -> utils.AttributeDict:
    #     assert isinstance(self.calls, KucoinAPI)
    #     """
    #         Get all currencies in an account, or sort by symbol/account_id
    #         Args:
    #             symbol (Optional): Filter by particular symbol
    #
    #             These arguments are mutually exclusive
    #     """
    #     #account_id = super().account()
    #     #symbol = super().get_account(symbol=symbol)
    #     needed = self.needed['get_account']
    #     """
    #     {
    #         "currency": "KCS",
    #         "balance": "1000000060.6299",
    #         "available": "1000000060.6299",
    #         "holds": "0"
    #     }
    #     """
    #
    #     account = self.calls.get_accounts()

    @utils.order_protection
    def market_order(self, symbol, side, size) -> MarketOrder:
        """
            Used for buying or selling market orders
            Args:
                symbol: currency to buy
                side: buy/sell
                size: desired amount of base currency to buy or sell
        """
        assert isinstance(self.calls, KucoinAPI)
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

        response = self.calls.Trade.create_market_order(symbol, side, size=size)
        response_details = self.calls.Trade.get_order_details(response)

        if "msg" in response:
            raise InvalidOrder("Invalid Order: " + response["msg"])
        response_details["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
        response_details = utils.isolate_specific(needed, response_details)
        return MarketOrder(order, response_details, self)

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
        assert isinstance(self.calls, KucoinAPI)
        needed = self.needed['limit_order']

        order = {
            'symbol': symbol,
            'size': size,
            'side': side,
            'price': price,
            'type': 'limit',
        }
        response = self.calls.Trade.create_limit_order(symbol, side, price, size=size)
        response_details = self.calls.Trade.get_order_details(response)

        if "msg" in response:
            raise InvalidOrder("Invalid Order: " + response["msg"])
        response_details["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
        response_details = utils.isolate_specific(needed, response_details)
        return LimitOrder(order, response_details, self)

    def cancel_order(self, symbol, order_id) -> dict:
        assert isinstance(self.calls, KucoinAPI)
        """
        Returns:
           dict: Containing the order_id of cancelled order. Example::
           { "cancelledOrderIds": ["c5ab5eae-76be-480e-8961-00792dc7e138"]}
        """
        return {"order_id": self.calls.Trade.cancel_order(order_id)}

    def get_open_orders(self, symbol: str = None) -> list:
        assert isinstance(self.calls, KucoinAPI)
        """
        List open orders.
        """
        """
        {
            "currentPage": 1,
            "pageSize": 1,
            "totalNum": 153408,
            "totalPage": 153408,
            "items": [
              {
                "id": "5c35c02703aa673ceec2a168",   //orderid
                "symbol": "BTC-USDT",   //symbol
                "opType": "DEAL",      // operation type: DEAL
                "type": "limit",       // order type,e.g. limit,market,stop_limit.
                "side": "buy",         // transaction direction,include buy and sell
                "price": "10",         // order price
                "size": "2",           // order quantity
                "funds": "0",          // order funds
                "dealFunds": "0.166",  // deal funds
                "dealSize": "2",       // deal quantity
                "fee": "0",            // fee
                "feeCurrency": "USDT", // charge fee currency
                "stp": "",             // self trade prevention,include CN,CO,DC,CB
                "stop": "",            // stop type
                "stopTriggered": false,  // stop order is triggered
                "stopPrice": "0",      // stop price
                "timeInForce": "GTC",  // time InForce,include GTC,GTT,IOC,FOK
                "postOnly": false,     // postOnly
                "hidden": false,       // hidden order
                "iceberg": false,      // iceberg order
                "visibleSize": "0",    // display quantity for iceberg order
                "cancelAfter": 0,      // cancel orders time，requires timeInForce to be GTT
                "channel": "IOS",      // order source
                "clientOid": "",       // user-entered order unique mark
                "remark": "",          // remark
                "tags": "",            // tag order source
                "isActive": false,     // status before unfilled or uncancelled
                "cancelExist": false,   // order cancellation transaction record
                "createdAt": 1547026471000,  // create time
                "tradeType": "TRADE"
              }
            ]
         }
        """
        if symbol is None:
            open_orders = list(self.calls.Trade.get_order_list())
        else:
            open_orders = list(self.calls.Trade.get_order_list(symbol=symbol))

        if len(open_orders) == 0:
            return []
        if open_orders[0] == 'msg':
            raise InvalidOrder("Invalid Order: " + str(open_orders))

        for i in range(len(open_orders)):
            open_orders[i]["created_at"] = utils.epoch_from_ISO8601(open_orders[i]["createdAt"])
            needed = self.choose_order_specificity(open_orders[i]['type'])
            open_orders[i] = utils.isolate_specific(needed, open_orders[i])

        return open_orders

    def get_order(self, symbol, order_id) -> dict:
        assert isinstance(self.calls, KucoinAPI)
        """
        {
            "id": "5c35c02703aa673ceec2a168",
            "symbol": "BTC-USDT",
            "opType": "DEAL",
            "type": "limit",
            "side": "buy",
            "price": "10",
            "size": "2",
            "funds": "0",
            "dealFunds": "0.166",
            "dealSize": "2",
            "fee": "0",
            "feeCurrency": "USDT",
            "stp": "",
            "stop": "",
            "stopTriggered": false,
            "stopPrice": "0",
            "timeInForce": "GTC",
            "postOnly": false,
            "hidden": false,
            "iceberg": false,
            "visibleSize": "0",
            "cancelAfter": 0,
            "channel": "IOS",
            "clientOid": "",
            "remark": "",
            "tags": "",
            "isActive": false,
            "cancelExist": false,
            "createdAt": 1547026471000,
            "tradeType": "TRADE"
        }
        """
        response = self.calls.Trade.get_order_details(order_id)

        if 'msg' in response:
            raise APIException("Invalid: " + str(response['message']) + ", was the order canceled?")
        response["createdAt"] = utils.epoch_from_ISO8601(response["createdAt"])

        if response['type'] == 'market':
            needed = self.needed['market_order']
        elif response['type'] == 'limit':
            needed = self.needed['limit_order']
        else:
            needed = self.needed['market_order']

        return utils.isolate_specific(needed, response)

    def get_fees(self) -> dict:
        assert isinstance(self.calls, KucoinAPI)
        needed = self.needed['get_fees']
        """
        {
            'maker_fee_rate': '0.0050',
            'taker_fee_rate': '0.0050',
            'usd_volume': '37.69'
        }
        """
        fees = self.calls.User.get_base_fee()
        return utils.isolate_specific(needed, fees)

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        assert isinstance(self.calls, KucoinAPI)
        resolution = blankly.time_builder.time_interval_to_seconds(resolution)

        # epoch_start, epoch_stop = super().get_product_history(symbol, epoch_start, epoch_stop, resolution)
        epoch_start = utils.convert_epochs(epoch_start)
        epoch_stop = utils.convert_epochs(epoch_stop)

        accepted_grans = [60, 300, 900, 3600, 21600, 86400]
        if resolution not in accepted_grans:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = accepted_grans[min(range(len(accepted_grans)),
                                            key=lambda i: abs(accepted_grans[i] - resolution))]

        resolution = int(resolution)

        # Figure out how many points are needed
        need = int((epoch_stop - epoch_start) / resolution)
        initial_need = need
        window_open = epoch_start
        history = []
        # Iterate while it is more than max
        while need > 300:
            # Close is always 300 points ahead
            window_close = window_open + 300 * resolution
            open_iso = utils.ISO8601_from_epoch(window_open)
            close_iso = utils.ISO8601_from_epoch(window_close)
            response = self.calls.Market.get_kline(symbol, open_iso, close_iso, resolution)
            if isinstance(response, dict):
                raise APIException(response['msg'])
            history = history + response

            window_open = window_close
            need -= 300
            time.sleep(.2)
            utils.update_progress((initial_need - need) / initial_need)

        # Fill the remainder
        open_iso = utils.ISO8601_from_epoch(window_open)
        close_iso = utils.ISO8601_from_epoch(epoch_stop)
        response = self.calls.Market.get_kline(symbol, open_iso, close_iso, resolution)
        if isinstance(response, dict):
            raise APIException(response['message'])
        history_block = history + response
        history_block.sort(key=lambda x: x[0])

        df = pd.DataFrame(history_block, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        # df[['time']] = df[['time']].astype(int)
        # Have to cast this for some reason
        df[['time']] = df[['time']].astype(int)
        df[['low', 'high', 'open', 'close', 'volume']] = df[['low', 'high', 'open', 'close', 'volume']].astype(float)

        return df

    def get_order_filter(self, symbol: str):
        response = self.calls.get_products()
        products = None
        for i in response:
            if i["id"] == symbol:
                products = i
                break

        if products is None:
            raise LookupError("Specified market not found")

        base_min_size = float(products.pop('base_min_size'))
        base_max_size = float(products.pop('base_max_size'))
        base_increment = float(products.pop('base_increment'))

        return {
            "symbol": products.pop('id'),
            "base_asset": products.pop('base_currency'),
            "quote_asset": products.pop('quote_currency'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": base_increment,  # Specifies the minimum increment
                # for the base_asset.
                "price_increment": float(products['quote_increment']),

                "min_price": float(products['quote_increment']),
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,

                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": base_increment,  # Specifies the minimum increment

                "quote_increment": float(products.pop('quote_increment')),  # Specifies the min order price as well
                # as the price increment.
                "buy": {
                    "min_funds": float(products['min_market_funds']),
                    "max_funds": float(products['max_market_funds']),
                },
                "sell": {
                    "min_funds": float(products.pop('min_market_funds')),
                    "max_funds": float(products.pop('max_market_funds')),
                },
            },
            "exchange_specific": {**products}
        }

    def get_price(self, symbol) -> float:
        assert isinstance(self.calls, KucoinAPI)
        response = self.calls.Market.get_ticker(symbol)
        if 'msg' in response:
            raise APIException("Error: " + response['message'])
        return float(response['price'])
