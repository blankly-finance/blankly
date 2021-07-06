"""
    Logic to provide consistency across exchanges
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
import warnings

import binance.exceptions
import pandas as pd

import Blankly.utils.exceptions as exceptions
import Blankly.utils.utils
import Blankly.utils.utils as utils
from Blankly.exchanges.orders.limit_order import LimitOrder
from Blankly.exchanges.orders.market_order import MarketOrder
from Blankly.exchanges.interfaces.currency_Interface import CurrencyInterface


class BinanceInterface(CurrencyInterface):
    def __init__(self, exchange_name, authenticated_API):
        super().__init__(exchange_name, authenticated_API)

    def init_exchange(self):
        try:
            account = self.calls.get_account()
        except binance.exceptions.BinanceAPIException:
            raise exceptions.APIException("Invalid API Key, IP, or permissions for action - are you trying "
                                          "to use your normal exchange keys while in sandbox mode?")
        self.__exchange_properties = {
            "maker_fee_rate": account['makerCommission'] / 100,
            "taker_fee_rate": account['takerCommission'] / 100,
            "buyer_fee_rate": account['buyerCommission'] / 100,  # I'm not sure of the case when these are nonzero
            "seller_fee_rate": account['sellerCommission'] / 100,
        }
        symbols = self.calls.get_exchange_info()["symbols"]
        assets = []
        for i in symbols:
            assets.append(i["baseAsset"])
            assets.append(i["quoteAsset"])

        # Because these come down as trading pairs we have to filter for duplicates
        filtered_base_assets = []
        for i in assets:
            # TODO replace this with a lambda function using the filter method
            if i not in filtered_base_assets:
                filtered_base_assets.append(i)
        self.__available_currencies = filtered_base_assets

    def get_products(self):
        needed = [["currency_id", str],
                  ["base_currency", str],
                  ["quote_currency", str],
                  ["base_min_size", float],
                  ["base_max_size", float],
                  ["base_increment", float]]
        """
        This is a section of the symbols array
        [
            {
                "symbol": "BTCUSD",
                "status": "TRADING",
                "baseAsset": "BTC",
                "baseAssetPrecision": 8,
                "quoteAsset": "USD",
                "quotePrecision": 4,
                "quoteAssetPrecision": 4,
                "baseCommissionPrecision": 8,
                "quoteCommissionPrecision": 2,
                "orderTypes": [
                    "LIMIT",
                    "LIMIT_MAKER",
                    "MARKET",
                    "STOP_LOSS_LIMIT",
                    "TAKE_PROFIT_LIMIT",
                ],
                "icebergAllowed": True,
                "ocoAllowed": True,
                "quoteOrderQtyMarketAllowed": True,
                "isSpotTradingAllowed": True,
                "isMarginTradingAllowed": False,
                "filters": [
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0.0100",
                        "maxPrice": "100000.0000",
                        "tickSize": "0.0100",
                    },
                    {
                        "filterType": "PERCENT_PRICE",
                        "multiplierUp": "5",
                        "multiplierDown": "0.2",
                        "avgPriceMins": 5,
                    },
                    {
                        "filterType": "LOT_SIZE",
                        "minQty": "0.00000100",
                        "maxQty": "9000.00000000",
                        "stepSize": "0.00000100",
                    },
                    {
                        "filterType": "MIN_NOTIONAL",
                        "minNotional": "10.0000",
                        "applyToMarket": True,
                        "avgPriceMins": 5,
                    },
                    {"filterType": "ICEBERG_PARTS", "limit": 10},
                    {
                        "filterType": "MARKET_LOT_SIZE",
                        "minQty": "0.00000000",
                        "maxQty": "3200.00000000",
                        "stepSize": "0.00000000",
                    },
                    {"filterType": "MAX_NUM_ORDERS", "maxNumOrders": 200},
                    {"filterType": "MAX_NUM_ALGO_ORDERS", "maxNumAlgoOrders": 5},
                ],
                "permissions": ["SPOT"],
            },
        ]
        """
        products = self.calls.get_exchange_info()["symbols"]
        for i in range(len(products)):
            # Rename needed
            products[i]["currency_id"] = products[i]["baseAsset"] + "-" + products[i]["quoteAsset"]
            products[i]["base_currency"] = products[i].pop("baseAsset")
            products[i]["quote_currency"] = products[i].pop("quoteAsset")
            filters = products[i]["filters"]
            # Iterate to find the next few
            min_qty = None
            max_qty = None
            base_increment = None
            for filters_array in filters:
                if filters_array["filterType"] == "LOT_SIZE":
                    min_qty = filters_array["minQty"]
                    max_qty = filters_array["maxQty"]
                    base_increment = filters_array["stepSize"]
                    break
            products[i]["base_min_size"] = min_qty
            products[i]["base_max_size"] = max_qty
            products[i]["base_increment"] = base_increment
            # Isolate keys unimportant for the interface's functionality
            products[i] = utils.isolate_specific(needed, products[i])
        return products

    def get_account(self, currency=None) -> utils.AttributeDict:
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency (Optional): Filter by particular currency

            These arguments are mutually exclusive
        Coinbase Pro: get_account
        Binance: get_account["balances"]
        """
        currency = super().get_account(currency=currency)

        needed = self.needed['get_account']

        # TODO this should really use the get_asset_balance() function from binance.
        """
        {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": true,
            "canWithdraw": true,
            "canDeposit": true,
            "balances": [
                {
                    "asset": "BTC",
                    "free": "4723846.89208129",
                    "locked": "0.00000000"
                },
                {
                    "asset": "LTC",
                    "free": "4763368.68006011",
                    "locked": "0.00000000"
                }
            ]
        }
        """
        renames = [
            ["asset", "currency"],
            ["free", "available"],
            ["locked", "hold"],
        ]

        accounts = self.calls.get_account()["balances"]

        # Isolate for currency, warn if not found or default to just returning a parsed version
        if currency is not None:
            if currency in self.__available_currencies:
                for i in range(len(accounts)):
                    # If it was in the accounts return we can just isolate & parse
                    if accounts[i]["asset"] == currency:
                        accounts = utils.rename_to(renames, accounts[i])
                        parsed_value = utils.isolate_specific(needed, accounts)
                        return utils.AttributeDict({
                            'available': parsed_value['available'],
                            'hold': parsed_value['hold']
                        })
                # If not just return a default 0 value. This is safe because we already checked if the currency
                #  was valid
                return utils.AttributeDict({
                    "available": 0.0,
                    "hold": 0.0
                })
            else:
                raise LookupError("Currency not found")

        # Binance only returns things you own, so extract those - scan and add that to the array.
        # We can fill it to a balance of zero later
        owned_assets = []
        for i in accounts:
            owned_assets.append(i['asset'])
        # Create an empty list for return
        parsed_dictionary = {}
        # Iterate through
        for i in self.__available_currencies:
            # Iterate through everything binance returned
            found = False
            for index, val in enumerate(accounts):
                # If the current available currency matches one from binance
                if val['asset'] == i:
                    # Do the normal thing above and append
                    mutated = utils.rename_to(renames, val)
                    mutated = utils.isolate_specific(needed, mutated)
                    parsed_dictionary[mutated['currency']] = utils.AttributeDict({
                        'available': mutated['available'],
                        'hold': mutated['hold']
                    })
                    found = True
            # If it wasn't found just default here
            if not found:
                parsed_dictionary[i] = utils.AttributeDict({
                    'available': 0.0,
                    'hold': 0.0
                })
        return utils.AttributeDict(parsed_dictionary)

    def market_order(self, product_id, side, funds) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            product_id: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
        """
        needed = self.needed['market_order']
        """
        Response RESULT:

        .. code-block:: python

        {
            "symbol": "BTCUSDT",        <-- Similar
            "orderId": 28,      <-- Similar
            "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
            "transactTime": 1507725176595,      <-- Similar
            "price": "0.00000000",      <-- Similar
            "origQty": "10.00000000",       <-- Similar
            "executedQty": "10.00000000",
            "status": "FILLED",     <-- Similar
            "timeInForce": "GTC",       <-- Similar
            "type": "MARKET",       <-- Similar
            "side": "SELL"      <-- Similar
        }
        
        Actual response buying 20 dollars worth
        {
            'symbol': 'BTCUSDT', 
            'orderId': 3038554, 
            'orderListId': -1, 
            'clientOrderId': 'xJqha6DQgdYHNdxuVqV2BZ', 
            'transactTime': 1623800280187, 
            'price': '0.00000000', 
            'origQty': '0.00049600', 
            'executedQty': '0.00049600', 
            'cummulativeQuoteQty': '19.99128000', 
            'status': 'FILLED', 
            'timeInForce': 'GTC', 
            'type': 'MARKET', 
            'side': 'BUY', 
            'fills': [
                {
                    'price': '40305.00000000', 
                    'qty': '0.00049600', 
                    'commission': '0.00000000', 
                    'commissionAsset': 'BTC', 
                    'tradeId': 564349
                }
            ]
        }
        """
        renames = [
            ["symbol", "product_id"],
            ["orderId", "id"],
            ["transactTime", "created_at"],
            ["origQty", "size"],
            ["timeInForce", "time_in_force"],
            ["cummulativeQuoteQty", "funds"]
        ]
        order = {
            'funds': funds,
            'side': side,
            'product_id': product_id,
            'type': 'market'
        }
        modified_product_id = utils.to_exchange_coin_id(product_id, "binance")
        # The interface here will be the query of order status from this object, because orders are dynamic
        # creatures
        response = self.calls.order_market(symbol=modified_product_id, side=side, quoteOrderQty=funds)
        response['side'] = response['side'].lower()
        response['type'] = response['type'].lower()
        response['status'] = super().homogenize_order_status('binance', response['status'].lower())
        response["transactTime"] = response["transactTime"] / 1000
        response = utils.rename_to(renames, response)
        response = utils.isolate_specific(needed, response)
        return MarketOrder(order, response, self)

    def limit_order(self, product_id, side, price, size) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
        """
        needed = self.needed['limit_order']
        """Send in a new limit order

        Any order with an icebergQty MUST have timeInForce set to GTC.

        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: str
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: str
        :param timeInForce: default Good till cancelled
        :type timeInForce: str
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param icebergQty: Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
        :type icebergQty: decimal
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceRequestException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException,
        BinanceOrderMinPriceException, BinanceOrderMinTotalException,
        BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        order = {
            'size': size,
            'side': side,
            'price': price,
            'product_id': product_id,
            'type': 'limit'
        }
        modified_product_id = utils.to_exchange_coin_id(product_id, 'binance')
        response = self.calls.order_limit(symbol=modified_product_id, side=side, price=price, quantity=size)
        renames = [
            ["symbol", "product_id"],
            ["orderId", "id"],
            ["transactTime", "created_at"],
            ["origQty", "size"],
            ["timeInForce", "time_in_force"],
        ]
        response['side'] = response['side'].lower()
        response['type'] = response['type'].lower()
        response['status'] = super().homogenize_order_status('binance', response['status'].lower())
        response['symbol'] = utils.to_blankly_coin_id(response['symbol'], 'binance')
        response = utils.rename_to(renames, response)
        response = utils.isolate_specific(needed, response)
        return LimitOrder(order, response, self)

    def cancel_order(self, currency_id, order_id) -> dict:
        """Cancel an active order. Either orderId or origClientOrderId must be sent.

        https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#cancel-order-trade

        :returns: API response

        .. code-block:: python

        {
          "symbol": "LTCBTC",
          "origClientOrderId": "myOrder1",
          "orderId": 4,
          "orderListId": -1, //Unless part of an OCO, the value will always be -1.
          "clientOrderId": "cancelMyOrder1",
          "price": "2.00000000",
          "origQty": "1.00000000",
          "executedQty": "0.00000000",
          "cummulativeQuoteQty": "0.00000000",
          "status": "CANCELED",
          "timeInForce": "GTC",
          "type": "LIMIT",
          "side": "BUY"
        }

        :raises: BinanceRequestException, BinanceAPIException

        """
        needed = self.needed['cancel_order']
        renames = [
            ["orderId", "order_id"]
        ]
        currency_id = utils.to_exchange_coin_id(currency_id, 'binance')
        response = self.calls.cancel_order(symbol=currency_id, orderId=order_id)
        response = utils.rename_to(renames, response)
        return utils.isolate_specific(needed, response)

    def get_open_orders(self, product_id=None):
        """
        List open orders.
        """
        """
        [
            {
                "symbol": "LTCBTC",
                "orderId": 1,
                "orderListId": -1, //Unless OCO, the value will always be -1
                "clientOrderId": "myOrder1",
                "price": "0.1",
                "origQty": "1.0",    <- what are these??
                "executedQty": "0.0",    <- what are these??
                "cummulativeQuoteQty": "0.0",    <- what are these??
                "status": "NEW",
                "timeInForce": "GTC",
                "type": "LIMIT",
                "side": "BUY",
                "stopPrice": "0.0",
                "icebergQty": "0.0",
                "time": 1499827319559,
                "updateTime": 1499827319559,
                "isWorking": true,
                "origQuoteOrderQty": "0.000000"    <- what are these??
            }
        ]
        """
        renames = [
            ["orderId", "id"],
            ["origQty", "size"],
            ["symbol", "product_id"],
            ["cummulativeQuoteQty", "funds"],
            ["time", "created_at"]
        ]

        if product_id is not None:
            product_id = utils.to_exchange_coin_id(product_id, "binance")
            orders = self.calls.get_open_orders(symbol=product_id)
        else:
            orders = self.calls.get_open_orders()

        for i in range(len(orders)):
            orders[i] = utils.rename_to(renames, orders[i])
            orders[i]['type'] = orders[i]['type'].lower()
            orders[i]['side'] = orders[i]['side'].lower()
            orders[i]['status'] = super().homogenize_order_status('binance', orders[i]['status'].lower())
            orders[i]['created_at'] = orders[i]['created_at'] / 1000
            needed = self.choose_order_specificity(orders[i]['type'])
            orders[i] = utils.isolate_specific(needed, orders[i])
            orders[i]['product_id'] = utils.to_blankly_coin_id(orders[i]['product_id'], 'binance', quote_guess=None)

        return orders

    def get_order(self, currency_id, order_id) -> dict:
        """
        :param symbol: required
        :type symbol: str
        :param orderId: The unique order id
        :type orderId: int
        :param origClientOrderId: optional
        :type origClientOrderId: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        {
            "symbol": "LTCBTC",
            "orderId": 1,
            "clientOrderId": "myOrder1",
            "price": "0.1",
            "origQty": "1.0",
            "executedQty": "0.0",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
            "stopPrice": "0.0",
            "icebergQty": "0.0",
            "time": 1499827319559
        }
        """
        renames = [
            ["orderId", "id"],
            ["origQty", "size"],
            ["symbol", "product_id"],
            ["cummulativeQuoteQty", "funds"],
            ["time", "created_at"],
            ["timeInForce", "time_in_force"]
        ]

        currency_id = utils.to_exchange_coin_id(currency_id, 'binance')
        response = self.calls.get_order(symbol=currency_id, orderId=int(order_id))

        response = utils.rename_to(renames, response)
        response['type'] = response['type'].lower()
        response['side'] = response['side'].lower()
        response['status'] = super().homogenize_order_status('binance', response['status'].lower())
        response['created_at'] = response['created_at']/1000
        response['product_id'] = utils.to_blankly_coin_id(response['product_id'], 'binance')
        needed = self.choose_order_specificity(response['type'])
        response = utils.isolate_specific(needed, response)

        return response

    """
    Coinbase Pro: get_fees
    Binance: get_trade_fee
    """

    def get_fees(self) -> dict:
        needed = self.needed['get_fees']
        """
        {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": true,
            "canWithdraw": true,
            "canDeposit": true,
            "balances": [
                {
                    "asset": "BTC",
                    "free": "4723846.89208129",
                    "locked": "0.00000000"
                },
                {
                    "asset": "LTC",
                    "free": "4763368.68006011",
                    "locked": "0.00000000"
                }
            ]
        }
        """
        # TODO: make sure this supports with Binance Coin (BNB) discount
        account = self.calls.get_account()
        # Get rid of the stuff we really don't need this time
        account.pop('canTrade')
        account.pop('canWithdraw')
        account.pop('canDeposit')
        account.pop('balances')
        # Rename makers and takers
        account['maker_fee_rate'] = account.pop('makerCommission') / 100
        account['taker_fee_rate'] = account.pop('takerCommission') / 100
        # Isolate
        return utils.isolate_specific(needed, account)

    """
    Coinbase Pro: get_account_history
    Binance:
        get_deposit_history
        get_withdraw_history

    """

    def get_product_history(self, product_id, epoch_start, epoch_stop, resolution):
        """
        Returns the product history from an exchange
        Args:
            product_id: Blankly product ID format (BTC-USD)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            resolution: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
        """

        resolution = Blankly.time_builder.time_interval_to_seconds(resolution)

        epoch_start, epoch_stop = super().get_product_history(product_id, epoch_start, epoch_stop, resolution)

        epoch_start = int(epoch_start)
        epoch_stop = int(epoch_stop)

        accepted_grans = [60, 180, 300, 900, 1800, 3600, 7200, 14400,
                          21600, 28800, 43200, 86400, 259200, 604800, 2592000]
        if resolution not in accepted_grans:
            warnings.warn("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = accepted_grans[min(range(len(accepted_grans)),
                                            key=lambda i: abs(accepted_grans[i] - resolution))]
        lookup_dict = {
            60: "1m",
            180: "3m",
            300: "5m",
            900: "15m",
            1800: "30m",
            3600: "1h",
            7200: "2h",
            14400: "4h",
            21600: "6h",
            28800: "8h",
            43200: "12h",
            86400: "1d",
            259200: "3d",
            604800: "1w",
            2592000: "1M"
        }
        gran_string = lookup_dict[resolution]

        # Figure out how many points are needed
        need = int((epoch_stop - epoch_start) / resolution)
        initial_need = need
        window_open = epoch_start
        history = []

        # Convert coin id to binance coin
        product_id = utils.to_exchange_coin_id(product_id, 'binance')
        while need > 1000:
            # Close is always 300 points ahead
            window_close = int(window_open + 1000 * resolution)
            history = history + self.calls.get_klines(symbol=product_id, startTime=window_open * 1000,
                                                      endTime=window_close * 1000, interval=gran_string,
                                                      limit=1000)

            window_open = window_close
            need -= 1000
            time.sleep(.2)
            utils.update_progress((initial_need - need) / initial_need)

        # Fill the remainder
        history_block = history + self.calls.get_klines(symbol=product_id, startTime=window_open * 1000,
                                                        endTime=epoch_stop * 1000, interval=gran_string,
                                                        limit=1000)

        data_frame = pd.DataFrame(history_block, columns=['time', 'open', 'high', 'low', 'close', 'volume',
                                                          'close time', 'quote asset volume', 'number of trades',
                                                          'taker buy base asset volume',
                                                          'taker buy quote asset volume', 'ignore'])
        # Clear the ignore column, why is that there binance?
        del data_frame['ignore']
        # Want them in this order: ['time (epoch)', 'low', 'high', 'open', 'close', 'volume']

        # Cast dataframe
        data_frame = data_frame.astype({'time': int,
                                        'open': float,
                                        'high': float,
                                        'low': float,
                                        'close': float,
                                        'volume': float,
                                        'close time': int,
                                        'quote asset volume': float,
                                        'number of trades': int,
                                        'taker buy base asset volume': float,
                                        'taker buy quote asset volume': float
                                        })

        # Convert time to seconds
        data_frame['time'] = data_frame['time'].div(1000)

        return data_frame.reindex(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    """
    Coinbase Pro: Get Currencies
    Binance: get_products
    """

    def get_market_limits(self, product_id):
        """
        Optimally we'll just remove the filter section and make the returns accurate
        {
            "symbol": "BTCUSD",
            "status": "TRADING",
            "baseAsset": "BTC",
            "baseAssetPrecision": 8,
            "quoteAsset": "USD",
            "quotePrecision": 4,
            "quoteAssetPrecision": 4,
            "baseCommissionPrecision": 8,
            "quoteCommissionPrecision": 2,
            "orderTypes": [
                "LIMIT",
                "LIMIT_MAKER",
                "MARKET",
                "STOP_LOSS_LIMIT",
                "TAKE_PROFIT_LIMIT",
            ],
            "icebergAllowed": True,
            "ocoAllowed": True,
            "quoteOrderQtyMarketAllowed": True,
            "isSpotTradingAllowed": True,
            "isMarginTradingAllowed": False,
            "filters": [
                {
                    "filterType": "PRICE_FILTER",
                    "minPrice": "0.0100",
                    "maxPrice": "100000.0000",
                    "tickSize": "0.0100",
                },
                {
                    "filterType": "PERCENT_PRICE",
                    "multiplierUp": "5",
                    "multiplierDown": "0.2",
                    "avgPriceMins": 5,
                },
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00000100",
                    "maxQty": "9000.00000000",
                    "stepSize": "0.00000100",
                },
                {
                    "filterType": "MIN_NOTIONAL",
                    "minNotional": "10.0000",
                    "applyToMarket": True,
                    "avgPriceMins": 5,
                },
                {"filterType": "ICEBERG_PARTS", "limit": 10},
                {
                    "filterType": "MARKET_LOT_SIZE",
                    "minQty": "0.00000000",
                    "maxQty": "3200.00000000",
                    "stepSize": "0.00000000",
                },
                {"filterType": "MAX_NUM_ORDERS", "maxNumOrders": 200},
                {"filterType": "MAX_NUM_ALGO_ORDERS", "maxNumAlgoOrders": 5},
            ],
            "permissions": ["SPOT"],
        },
        """

        converted_symbol = utils.to_exchange_coin_id(product_id, 'binance')
        current_price = None
        symbol_data = self.calls.get_exchange_info()["symbols"]
        for i in symbol_data:
            if i["symbol"] == converted_symbol:
                symbol_data = i
                current_price = float(self.calls.get_avg_price(symbol=converted_symbol)['price'])
                break
        if current_price is None:
            raise LookupError("Specified market not found")

        filters = symbol_data["filters"]
        hard_min_price = float(filters[0]["minPrice"])
        hard_max_price = float(filters[0]["maxPrice"])
        quote_increment = float(filters[0]["tickSize"])

        percent_min_price = float(filters[1]["multiplierDown"]) * current_price
        percent_max_price = float(filters[1]["multiplierUp"]) * current_price

        min_quantity = float(filters[2]["minQty"])
        max_quantity = float(filters[2]["maxQty"])
        base_increment = float(filters[2]["stepSize"])

        max_orders = int(filters[6]["maxNumOrders"])

        if percent_min_price < hard_min_price:
            min_price = hard_min_price
        else:
            min_price = percent_min_price

        if percent_max_price > hard_max_price:
            max_price = hard_max_price
        else:
            max_price = percent_max_price

        return {
            "market": product_id,
            "base_currency": symbol_data["baseAsset"],
            "quote_currency": symbol_data["quoteAsset"],
            "base_min_size": min_quantity,  # Minimum size to buy
            "base_max_size": max_quantity,  # Maximum size to buy
            "quote_increment": quote_increment,  # Specifies the min order price as well as the price increment.
            "base_increment": base_increment,  # Specifies the minimum increment for the base_currency.
            "max_orders": max_orders,
            "min_price": min_price,
            "max_price": max_price,
            "fractional_limit": False,
            "exchange_specific": {}
        }

    def get_price(self, currency_pair) -> float:
        """
        Returns just the price of a currency pair.
        """
        currency_pair = utils.to_exchange_coin_id(currency_pair, "binance")
        response = self.calls.get_symbol_ticker(symbol=currency_pair)
        return float(response['price'])
