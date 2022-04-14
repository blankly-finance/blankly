"""
    Base authentication for kucoin
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

import time

import pandas as pd

import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils.exceptions import APIException, InvalidOrder


class KucoinInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):

        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 180, 300, 900, 1800,
                                                                              3600, 7200, 14400, 21600,
                                                                              28800, 43200, 86400, 604800])

        try:
            from kucoin import client as KucoinAPI
        except ImportError:
            raise ImportError("Please \"pip install kucoin-python\" to use kucoin with blankly.")

        self._market: KucoinAPI.Market = self.calls['market']
        self._trade: KucoinAPI.Trade = self.calls['trade']
        self._user: KucoinAPI.User = self.calls['user']


    def init_exchange(self):
        fees = self.calls['user'].get_base_fee()
        try:
            if fees['msg'] == "Invalid API Key":
                raise LookupError("Invalid API Key - are you trying to use your normal exchange keys "
                                  "while in sandbox mode? \nTry toggling the \'use_sandbox\' setting "
                                  "in your settings.json or check if the keys were input correctly into your "
                                  "keys.json.")
        except KeyError:
            pass

    @staticmethod
    def __correct_api_call(response):
        if isinstance(response, dict):
            if 'code' in response:
                if response['code'] == "200000":
                    return response['data']
                else:
                    try:
                        raise APIException(response['msg'])
                    except KeyError:
                        raise KeyError("Query failed but no exchange message found.")
            else:
                return response
        else:
            return response

    def get_products(self):
        needed = self.needed['get_products']
        """
        [
          {
            "symbol": "BTC-USDT",
            "name": "BTC-USDT",
            "baseCurrency": "BTC",
            "quoteCurrency": "USDT",
            "baseMinSize": "0.00000001",
            "quoteMinSize": "0.01",
            "baseMaxSize": "10000",
            "quoteMaxSize": "100000",
            "baseIncrement": "0.00000001",
            "quoteIncrement": "0.01",
            "priceIncrement": "0.00000001",
            "feeCurrency": "USDT",
            "enableTrading": true,
            "isMarginEnabled": true,
            "priceLimitRate": "0.1"
          }
        ]
        """
        products = self._market.get_symbol_list()
        products = self.__correct_api_call(products)
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
            Get all currencies in an account, or sort by symbol
            Args:
                symbol (Optional): Filter by particular symbol
                These arguments are mutually exclusive
        """
        symbol = super().get_account(symbol=symbol)

        """
        [
              {
                "id": "5bd6e9286d99522a52e458de",  //accountId
                "currency": "BTC",  //Currency
                "type": "main",     //Account type, including main and trade
                "balance": "237582.04299",  //Total assets of a currency
                "available": "237582.032",  //Available assets of a currency
                "holds": "0.01099" //Hold assets of a currency
              },
              {
                ...
              }
        """
        accounts = self._user.get_account_list()
        accounts = self.__correct_api_call(accounts)
        trade_accounts = []
        # Filter for only the trade accounts
        for i in accounts:
            if i['type'] == 'trade':
                trade_accounts.append(i)

        # If we have no positions this is a case that things can go wrong
        if isinstance(trade_accounts, dict):
            trade_accounts = []

        # We have to sort through it if the accounts are none
        if symbol is not None:
            for i in trade_accounts:
                if i["currency"] == symbol:
                    return utils.AttributeDict({
                        'available': float(i['available']),
                        'hold': float(i['holds'])
                    })

        parsed_dictionary = utils.AttributeDict({})

        # If the first loop didn't find it we'll try again here
        for i in range(len(trade_accounts)):
            parsed_dictionary[trade_accounts[i]['currency']] = utils.AttributeDict({
                'available': float(trade_accounts[i]['available']),
                'hold': float(trade_accounts[i]['holds'])
            })

        parsed_dictionary = utils.add_all_products(parsed_dictionary, self.get_products())

        if symbol is not None:
            if symbol in parsed_dictionary:
                return parsed_dictionary[symbol]
            else:
                raise KeyError(f'Could not find account for asset {symbol}')

        return parsed_dictionary

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
            'side': side,
            'size': size,
            'type': 'market',
        }

        response = self._trade.create_market_order(symbol, side, size=size)
        response = self.__correct_api_call(response)
        if "msg" in response:
            raise InvalidOrder("Invalid Order: " + response["msg"])

        response_details = self._trade.get_order_details(response['orderId'])
        """
        {
            "id": "5c35c02703aa673ceec2a168", //
            "symbol": "BTC-USDT", //
            "opType": "DEAL",
            "type": "limit", //
            "side": "buy", //
            "price": "10",
            "size": "2", //
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
            "isActive": false, //
            "cancelExist": false,
            "createdAt": 1547026471000, //
            "tradeType": "TRADE"
        }
        """

        response_details["created_at"] = response_details.pop('createdAt')
        response_details["status"] = response_details.pop('isActive')
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
        needed = self.needed['limit_order']

        order = {
            'symbol': symbol,
            'side': side,
            'size': size,
            'price': price,
            'type': 'limit',
        }
        response = self._trade.create_limit_order(symbol, side, size, price)
        response = self.__correct_api_call(response)
        if "msg" in response:
            raise InvalidOrder("Invalid Order: " + response["msg"])

        response_details = self._trade.get_order_details(response['orderId'])
        response_details = self.__correct_api_call(response_details)
        """
               {
                   "id": "5c35c02703aa673ceec2a168", //
                   "symbol": "BTC-USDT", //
                   "opType": "DEAL",
                   "type": "limit", //
                   "side": "buy", //
                   "price": "10",
                   "size": "2", //
                   "funds": "0",
                   "dealFunds": "0.166",
                   "dealSize": "2",
                   "fee": "0",
                   "feeCurrency": "USDT",
                   "stp": "",
                   "stop": "",
                   "stopTriggered": false,
                   "stopPrice": "0",
                   "timeInForce": "GTC", //
                   "postOnly": false,
                   "hidden": false,
                   "iceberg": false,
                   "visibleSize": "0",
                   "cancelAfter": 0,
                   "channel": "IOS",
                   "clientOid": "",
                   "remark": "",
                   "tags": "",
                   "isActive": false, //
                   "cancelExist": false,
                   "createdAt": 1547026471000, //
                   "tradeType": "TRADE"
               }
               """

        response_details["created_at"] = response_details.pop('createdAt')
        response_details["time_in_force"] = response_details.pop('timeInForce')
        response_details["status"] = response_details.pop('isActive')
        if response_details["status"]:
            response_details["status"] = 'pending'
        else:
            response_details["status"] = 'done'
        response_details = utils.isolate_specific(needed, response_details)
        return LimitOrder(order, response_details, self)

    def cancel_order(self, symbol, order_id) -> dict:
        """
        Returns:
           dict: Containing the order_id of cancelled order. Example::
           { "cancelledOrderIds": ["c5ab5eae-76be-480e-8961-00792dc7e138"]}
        """
        return {"order_id": self.__correct_api_call(self._trade.cancel_order(order_id)['cancelledOrderIds'][0])}

    def get_open_orders(self, symbol=None):
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
            open_orders = list(self.__correct_api_call(self._trade.get_order_list(status='active')["items"]))
        else:
            open_orders = list(self.__correct_api_call(self._trade.get_order_list(status='active', symbol=symbol)["items"]))

        if len(open_orders) == 0:
            return []
        if open_orders[0] == 'msg':
            raise APIException("Error: " + str(open_orders))

        for i in range(len(open_orders)):
            # open_orders[i]["createdAt"] = utils.epoch_from_ISO8601(open_orders[i]["createdAt"])
            needed = self.choose_order_specificity(open_orders[i]['type'])
            open_orders[i]["time_in_force"] = open_orders[i].pop('timeInForce')
            open_orders[i]["created_at"] = open_orders[i].pop('createdAt')
            open_orders[i]["status"] = open_orders[i].pop('isActive')
            if open_orders[i]["status"]:
                open_orders[i]["status"] = 'pending'
            else:
                open_orders[i]["status"] = 'done'

            open_orders[i] = utils.isolate_specific(needed, open_orders[i])

        return open_orders

    def get_order(self, symbol, order_id) -> dict:
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
        response = self._trade.get_order_details(order_id)
        response = self.__correct_api_call(response)

        if 'msg' in response:
            raise APIException("Invalid: " + str(response['msg']) + ", was the order canceled?")

        if isinstance(response['createdAt'], str):
            response["createdAt"] = utils.epoch_from_iso8601(response["createdAt"])

        if response['type'] == 'market':
            needed = self.needed['market_order']
        elif response['type'] == 'limit':
            needed = self.needed['limit_order']
        else:
            needed = self.needed['market_order']

        response["created_at"] = response.pop('createdAt')
        response["status"] = response.pop('isActive')
        if response["status"]:
            response["status"] = 'pending'
        else:
            response["status"] = 'done'
        response["time_in_force"] = response.pop('timeInForce')

        return utils.isolate_specific(needed, response)

    def get_fees(self, symbol) -> dict:
        needed = self.needed['get_fees']
        """
            {
                "code": "200000",
                "data": {
                    "takerFeeRate": "0.001",
                    "makerFeeRate": "0.001"
                }
            }
        """
        fees = self._user.get_base_fee()
        fees = self.__correct_api_call(fees)
        fees["taker_fee_rate"] = fees.pop('takerFeeRate')
        fees["maker_fee_rate"] = fees.pop('makerFeeRate')
        return utils.isolate_specific(needed, fees)

    def overridden_history(self, symbol, epoch_start, epoch_stop, resolution, **kwargs) -> pd.DataFrame:
        """
        Kucoin is strange because it's exclusive instead of inclusive. This generally invovles adding an extra
        datapoint so this is here to do some of that work
        """
        to = kwargs['to']

        if isinstance(to, str):
            epoch_start -= resolution
        elif isinstance(to, int):
            epoch_start = epoch_stop - (to * resolution)

        return self.__correct_api_call(self.get_product_history(symbol, epoch_start, epoch_stop, resolution))

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        """
        Returns the product history from an exchange
        Args:
            symbol: blankly product ID format (BTC-USD)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            resolution: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
        """
        resolution = blankly.time_builder.time_interval_to_seconds(resolution)

        epoch_start = int(utils.convert_epochs(epoch_start))
        epoch_stop = int(utils.convert_epochs(epoch_stop))

        accepted_grans = [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 28800, 43200, 86400, 604800]

        if resolution not in accepted_grans:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = accepted_grans[min(range(len(accepted_grans)),
                                            key=lambda i: abs(accepted_grans[i] - resolution))]

        resolution = int(resolution)

        epoch_start -= resolution

        lookup_dict = {
            60: '1min',
            180: '3min',
            300: '5min',
            900: '15min',
            1800: '30min',
            3600: '1hour',
            7200: '2hour',
            14400: '4hour',
            21600: '6hour',
            28800: '8hour',
            43200: '12hour',
            86400: '1day',
            604800: '1week',
        }
        gran_string = lookup_dict[resolution]

        # Figure out how many points are needed
        need = int((epoch_stop - epoch_start) / resolution)
        initial_need = need
        window_open = epoch_start
        history = []

        while need > 1500:
            # Close is always 300 points ahead
            window_close = int(window_open + 1500 * resolution)
            response = self._market.get_kline(symbol, gran_string,
                                              startAt=window_open, endAt=window_close)
            response = self.__correct_api_call(response)
            if isinstance(response, dict):
                raise APIException(response['msg'])
            history = history + response

            window_open = window_close
            need -= 1500
            time.sleep(1)
            utils.update_progress((initial_need - need) / initial_need)

        # Fill the remainder
        response = self._market.get_kline(symbol, gran_string,
                                          startAt=window_open, endAt=epoch_stop)
        response = self.__correct_api_call(response)
        if isinstance(response, dict):
            raise APIException(response['msg'])

        history = history + response
        history.sort(key=lambda x: x[0])

        df = pd.DataFrame(history, columns=['time', 'open', 'close', 'high', 'low', 'volume', 'turnover'])
        del df['turnover']

        # Have to cast this for some reason
        # df[['time']] = df[['time']].astype(float)
        df[['time']] = df[['time']].astype(int)
        df[['open', 'close', 'high', 'low', 'volume']] = df[['open', 'close', 'high', 'low', 'volume']].astype(float)

        try:
            epoch_start += resolution
            df = (df.iloc[int(-(epoch_stop-epoch_start)/resolution):]).reset_index(drop=True)
        except Exception:
            pass

        return df.reindex(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    def get_order_filter(self, symbol: str):
        """
        Returns:
        list: List of available currency pairs. Example::
           [
              {
                "symbol": "BTC-USDT",
                "name": "BTC-USDT",
                "baseCurrency": "BTC",
                "quoteCurrency": "USDT",
                "baseMinSize": "0.00000001",
                "quoteMinSize": "0.01",
                "baseMaxSize": "10000",
                "quoteMaxSize": "100000",
                "baseIncrement": "0.00000001",
                "quoteIncrement": "0.01",
                "priceIncrement": "0.00000001",
                "feeCurrency": "USDT",
                "enableTrading": true,
                "isMarginEnabled": true,
                "priceLimitRate": "0.1"
              }
           ]
        """
        response = self._market.get_symbol_list()
        response = self.__correct_api_call(response)
        products = None
        for i in response:
            if i["symbol"] == symbol:
                products = i
                break

        if products is None:
            raise LookupError("Specified market not found")

        base_min_size = float(products.pop('baseMinSize'))
        base_max_size = float(products.pop('baseMaxSize'))
        base_increment = float(products.pop('baseIncrement'))

        return {
            "symbol": products.pop('symbol'),
            "base_asset": products.pop('baseCurrency'),
            "quote_asset": products.pop('quoteCurrency'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": base_increment,  # Specifies the minimum increment
                # for the base_asset.
                "price_increment": float(products['quoteIncrement']),

                "min_price": float(products['quoteIncrement']),
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,

                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": base_max_size,  # Maximum size to buy
                "base_increment": base_increment,  # Specifies the minimum increment

                "quote_increment": float(products.pop('quoteIncrement')),  # Specifies the min order price as well
                # as the price increment.
                "buy": {
                    "min_funds": float(products['quoteMinSize']),
                    "max_funds": float(products['quoteMaxSize']),
                },
                "sell": {
                    "min_funds": float(products.pop('quoteMinSize')),
                    "max_funds": float(products.pop('quoteMaxSize')),
                },
            },
            "exchange_specific": {**products}
        }

    def get_price(self, symbol) -> float:
        """
        Returns the best bid price and size,
        the best ask price and size as well
        as the last traded price and the last traded size
        """
        """
         {
            "sequence": "1550467636704",
            "bestAsk": "0.03715004",
            "size": "0.17",
            "price": "0.03715005",
            "bestBidSize": "3.803",
            "bestBid": "0.03710768",
            "bestAskSize": "1.788",
            "time": 1550653727731
        }       
        """
        response = self._market.get_ticker(symbol)
        response = self.__correct_api_call(response)
        if 'msg' in response:
            raise APIException("Error: " + response['msg'])
        return float(response['price'])