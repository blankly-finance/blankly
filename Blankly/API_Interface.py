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
import secrets
import time
import warnings
import pandas as pd
import Blankly.utils.utils as utils
from Blankly.utils.exceptions import InvalidOrder
from Blankly.utils.purchases.limit_order import LimitOrder
from Blankly.utils.purchases.market_order import MarketOrder


class APIInterface:
    def __init__(self, exchange_name, authenticated_API):
        self.__exchange_name = exchange_name
        self.__calls = authenticated_API
        # Reload user preferences here
        self.__user_preferences = utils.load_user_preferences()
        self.__paper_trading = self.__user_preferences["settings"]["paper_trade"]
        self.__paper_trade_orders = []
        # TODO, improve creation of its own properties
        self.__exchange_properties = None
        # Some exchanges like binance will not return a value of 0.00 if there is no balance
        self.__available_currencies = {}
        self.__init_exchange__()

    def __init_exchange__(self):
        if self.__exchange_name == "coinbase_pro":
            fees = self.__calls.get_fees()
            try:
                if fees['message'] == "Invalid API Key":
                    raise ValueError("Invalid API Key - are you trying to use your normal exchange keys "
                                     "while in sandbox mode?")
            except KeyError:
                pass
            self.__exchange_properties = {
                "maker_fee_rate": fees['maker_fee_rate'],
                "taker_fee_rate": fees['taker_fee_rate']
            }
        if self.__exchange_name == "binance":
            account = self.__calls.get_account()
            self.__exchange_properties = {
                "maker_fee_rate": account['makerCommission']/100,
                "taker_fee_rate": account['takerCommission']/100,
                "buyer_fee_rate": account['buyerCommission']/100,  # I'm not sure of the case when these are nonzero
                "seller_fee_rate": account['sellerCommission']/100,
            }
            symbols = self.__calls.get_exchange_info()["symbols"]
            base_assets = []
            for i in symbols:
                base_assets.append(i["baseAsset"])
            self.__available_currencies = base_assets

    def __override_paper_trading(self, value):
        self.__paper_trading = bool(value)

    def get_calls(self):
        """
        Returns:
             The exchange's direct calls object. A Blankly Bot class should have immediate access to this by
             default
        """
        return self.__calls

    def get_exchange_type(self):
        return self.__exchange_name

    def get_products(self):
        needed = [["currency_id", str],
                  ["base_currency", str],
                  ["quote_currency", str],
                  ["base_min_size", float],
                  ["base_max_size", float],
                  ["base_increment", float]]
        if self.__exchange_name == "coinbase_pro":
            """
            [
                {
                    "id": "BTC-USD",
                    "base_currency": "BTC",
                    "quote_currency": "USD",
                    "base_min_size": "0.0001",
                    "base_max_size": "280",
                    "quote_increment": "0.01",
                    "base_increment": "0.00000001",
                    "display_name": "BTC/USD",
                    "min_market_funds": "5",
                    "max_market_funds": "1000000",
                    "margin_enabled": False,
                    "post_only": False,
                    "limit_only": False,
                    "cancel_only": False,
                    "trading_disabled": False,
                    "status": "online",
                    "status_message": "",
                },
            ]
            """
            products = self.__calls.get_products()
            for i in range(len(products)):
                # Rename needed
                products[i]["currency_id"] = products[i].pop("id")
                # Isolate unimportant
                products[i] = utils.isolate_specific(needed, products[i])
            return products
        elif self.__exchange_name == "binance":
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
            products = self.__calls.get_exchange_info()["symbols"]
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
                return utils.isolate_specific(needed, products[i])
            return products

    def get_account(self, currency=None, account_id=None):
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency: (Optional) Filter by particular currency
            account_id: (Optional) Filter by a particular account_id

            These arguments are mutually exclusive
        Coinbase Pro: get_account
        Binance: get_account["balances"]
        """
        if currency is not None:
            currency = utils.get_base_currency(currency)
        needed = [["currency", str],
                  ["available", float],
                  ["hold", float]]
        if currency is not None and account_id is not None:
            warnings.warn("One of \"account_id\" or \"currency\" must be empty. Defaulting to \"account_id\".")
            currency = None
        if self.__exchange_name == "coinbase_pro":
            if account_id is None:
                """
                [
                    {
                        "id": "71452118-efc7-4cc4-8780-a5e22d4baa53",
                        "currency": "BTC",
                        "balance": "0.0000000000000000",
                        "available": "0.0000000000000000",
                        "hold": "0.0000000000000000",
                        "profile_id": "75da88c5-05bf-4f54-bc85-5c775bd68254"
                    },
                    {
                        ...
                    }
                ]
                """
                accounts = self.__calls.get_accounts()
                # We have to sort through it if the accounts are none
                if currency is None:
                    # If this is also none we just return raw, which we do later
                    pass
                else:
                    for i in accounts:
                        if i["currency"] == currency:
                            parsed_value = utils.isolate_specific(needed, i)
                            return parsed_value
                    warnings.warn("Currency not found")
                for i in range(len(accounts)):
                    accounts[i] = utils.isolate_specific(needed, accounts[i])
                return accounts
            else:
                """
                {
                    "id": "a1b2c3d4",
                    "balance": "1.100",
                    "holds": "0.100",
                    "available": "1.00",
                    "currency": "USD"
                }
                """
                response = self.__calls.get_account(account_id)
                return utils.isolate_specific(needed, response)
        elif self.__exchange_name == "binance":
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
            if account_id is not None:
                warnings.warn("account_id parameter is not supported on binance, use currency instead. This parameter"
                              "will be removed soon.")

            accounts = self.__calls.get_account()["balances"]
            # Isolate for currency, warn if not found or default to just returning a parsed version
            if currency is not None:
                if currency in self.__available_currencies:
                    for i in range(len(accounts)):
                        if accounts[i]["asset"] == currency:
                            accounts = utils.rename_to(renames, accounts)
                            parsed_value = utils.isolate_specific(needed, accounts[i])
                            return parsed_value
                    return {
                        "currency": currency,
                        "available": 0.0,
                        "hold": 0.0
                    }
                else:
                    raise ValueError("Currency not found")

            # If binance returned something relevant, scan and add that to the array. If not just default to nothing
            owned_assets = [column[0] for column in accounts]
            # Fill this list for return
            filled_dict_list = []
            # Iterate through
            for i in self.__available_currencies:
                # Iterate through everything binance returned
                for index, val in enumerate(owned_assets):
                    # If the current available currency matches one from binance
                    if val == i:
                        # Do the normal thing above and append
                        accounts = utils.rename_to(renames, accounts)
                        accounts[index] = utils.isolate_specific(needed, accounts[index])
                        filled_dict_list.append({
                            accounts[index]
                        })
                        continue
                # If it wasn't found just default here
                filled_dict_list.append({
                    "currency": i,
                    "available": 0.0,
                    "hold": 0.0
                })
            return filled_dict_list

    def market_order(self, product_id, side, funds, **kwargs) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            product_id: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
            kwargs: specific arguments that may be used by each exchange, if exchange is known
        """
        order = None
        response = None
        needed = [
            ["product_id", str],
            ["id", str],
            ["created_at", float],
            ["funds", float],
            ["status", str],
            ["type", str],
            ["side", str]
        ]
        if self.__exchange_name == "coinbase_pro":
            """
            {
                'id': '8d3a6ea5-8d6d-4486-9c98-b266bae9a67c', 
                'product_id': 'BTC-USD', 
                'side': 'buy', 
                'stp': 'dc', 
                'funds': '39.92015968', 
                'specified_funds': '40', 
                'type': 'market', 
                'post_only': False, 
                'created_at': 1621015423.292914, 
                'fill_fees': '0', 
                'filled_size': '0', 
                'executed_value': '0', 
                'status': 'pending', 
                'settled': False
            }
            """
            order = {
                'funds': funds,
                'side': side,
                'product_id': product_id,
                'type': 'market'
            }
            if not self.__paper_trading:
                response = self.__calls.place_market_order(product_id, side, funds=funds)
                if "message" in response:
                    raise InvalidOrder("Invalid Order: " + response["message"])
                response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
            else:
                print("paper trading")
                creation_time = time.time()
                price = self.get_price(product_id)
                min_funds = float(self.get_market_limits(product_id)["exchange_specific"]["min_market_funds"])
                if funds < min_funds:
                    raise InvalidOrder("Invalid Order: funds is too small: " + str(min_funds))
                # Create coinbase pro-like id
                coinbase_pro_id = secrets.token_hex(nbytes=16)
                coinbase_pro_id = coinbase_pro_id[:8] + '-' + coinbase_pro_id[8:]
                coinbase_pro_id = coinbase_pro_id[:13] + '-' + coinbase_pro_id[13:]
                coinbase_pro_id = coinbase_pro_id[:18] + '-' + coinbase_pro_id[18:]
                coinbase_pro_id = coinbase_pro_id[:23] + '-' + coinbase_pro_id[23:]
                self.__paper_trade_orders.append({
                    'id': coinbase_pro_id,
                    'side': side,
                    'type': 'market',
                    'status': 'done',
                    'product_id': product_id,
                    'funds': funds-funds*float((self.__exchange_properties["maker_fee_rate"])),
                    'specified_funds': funds,
                    'post_only': False,
                    'created_at': creation_time,
                    'done_at': time.time(),
                    'done_reason': 'filled',
                    'fill_fees': funds*float((self.__exchange_properties["maker_fee_rate"])),
                    'filled_size': funds-funds*float((self.__exchange_properties["maker_fee_rate"]))/price,
                    'executed_value': funds-funds*float((self.__exchange_properties["maker_fee_rate"])),
                    'settled': True
                })
            response = utils.isolate_specific(needed, response)
        elif self.__exchange_name == "binance":
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
            """
            order = {
                'funds': funds,
                'side': side,
                'product_id': product_id,
                'type': 'market'
            }
            renames = [
                ["symbol", "product_id"],
                ["orderId", "id"],
                ["transactTime", "created_at"],
                ["origQty", "size"],
                ["timeInForce", "time_in_force"],
            ]
            modified_product_id = utils.to_exchange_coin_id(product_id, "binance")
            # The interface here will be the query of order status from this object, because orders are dynamic
            # creatures
            response = self.__calls.order_market(symbol=modified_product_id, side=side, quoteOrderQty=funds)
            response = utils.rename_to(renames, response)
            response = utils.isolate_specific(needed, response)
            response["transactTime"] = response["transactTime"]/1000
        return MarketOrder(order, response, self)

    def limit_order(self, product_id, side, price, size, **kwargs) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
            kwargs: specific arguments that may be used by each exchange, (if exchange is known)
        """
        order = None
        response = None
        needed = [
            ["product_id", str],
            ["id", str],
            ["created_at", int],
            ["price", float],
            ["size", float],
            ["status", str],
            ["time_in_force", str],
            ["type", str],
            ["side", str]
        ]
        if self.__exchange_name == "coinbase_pro":
            """
            {
                "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                "price": "0.10000000",
                "size": "0.01000000",
                "product_id": "BTC-USD",
                "side": "buy",
                "stp": "dc",
                "type": "limit",
                "time_in_force": "GTC",
                "post_only": false,
                "created_at": "2016-12-08T20:02:28.53864Z",
                "fill_fees": "0.0000000000000000",
                "filled_size": "0.00000000",
                "executed_value": "0.0000000000000000",
                "status": "pending",
                "settled": false
            }
            """
            order = {
                'size': size,
                'side': side,
                'price': price,
                'product_id': product_id,
                'type': 'limit'
            }
            response = self.__calls.place_limit_order(product_id, side, price, size=size)
            try:
                response = response["message"]
                raise InvalidOrder("Invalid Order: " + response)
            except KeyError:
                pass

            response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
            response = utils.isolate_specific(needed, response)
        elif self.__exchange_name == "binance":
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
            response = self.__calls.order_limit(symbol=modified_product_id, side=side, price=price, quantity=size,
                                                kwargs=kwargs)
            renames = [
                ["symbol", "product_id"],
                ["orderId", "id"],
                ["transactTime", "created_at"],
                ["origQty", "size"],
                ["timeInForce", "time_in_force"],
            ]
            response = utils.rename_to(renames, response)
            response = utils.isolate_specific(needed, response)
        return LimitOrder(order, response, self)

    """ 
    ATM it doesn't seem like the Binance library supports stop orders. 
    We need to add this when we implement our own.
    """
    # def stop_order(self, product_id, side, price, size, **kwargs):
    #     """
    #     Used for placing stop orders
    #     Args:
    #         product_id: currency to buy
    #         side: buy/sell
    #         price: price to set limit order
    #         size: amount of currency (like BTC) for the limit to be valued
    #         kwargs: specific arguments that may be used by each exchange, (if exchange is known)
    #     """
    #     if self.__exchange_name == "coinbase_pro":
    #         """
    #         {
    #             "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
    #             "price": "0.10000000",
    #             "size": "0.01000000",
    #             "product_id": "BTC-USD",
    #             "side": "buy",
    #             "stp": "dc",
    #             "type": "limit",
    #             "time_in_force": "GTC",
    #             "post_only": false,
    #             "created_at": "2016-12-08T20:02:28.53864Z",
    #             "fill_fees": "0.0000000000000000",
    #             "filled_size": "0.00000000",
    #             "executed_value": "0.0000000000000000",
    #             "status": "pending",
    #             "settled": false
    #         }
    #         """
    #         order = {
    #             'size': size,
    #             'side': side,
    #             'product_id': product_id,
    #             'type': 'stop'
    #         }
    #         self.__calls.placeOrder(product_id, side, price, size)
    #         response = self.__calls.place_market_order(product_id, side, price, size, kwargs=kwargs)
    #         return Purchase(order,
    #                         response,
    #                         self.__ticker_manager.get_ticker(product_id,
    #                                                          override_default_exchange_name="coinbase_pro"),
    #                         self.__exchange_properties)

    def cancel_order(self, currency_id, order_id) -> dict:
        if self.__exchange_name == "coinbase_pro":
            """
            Returns:
                list: Containing the order_id of cancelled order. Example::
                [ "c5ab5eae-76be-480e-8961-00792dc7e138" ]
            """
            return {"order_id": self.__calls.cancel_order(order_id)[0]}
        elif self.__exchange_name == "binance":
            """Cancel an active order. Either orderId or origClientOrderId must be sent.

            https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#cancel-order-trade

            :param symbol: required
            :type symbol: str
            :param orderId: The unique order id
            :type orderId: int
            :param origClientOrderId: optional
            :type origClientOrderId: str
            :param newClientOrderId: Used to uniquely identify this cancel. Automatically generated by default.
            :type newClientOrderId: str
            :param recvWindow: the number of milliseconds the request is valid for
            :type recvWindow: int

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
            renames = [
                ["orderId", "id"]
            ]
            needed = [
                ["id", str]
            ]
            response = self.__calls.cancel_order(symbol=currency_id, orderId=order_id)
            response = utils.rename_to(renames, response)
            return utils.isolate_specific(needed, response)

    def get_open_orders(self, product_id=None, **kwargs):
        """
        List open orders.
        """
        needed = [
            ["id", str],
            ["price", float],
            ["size", float],
            ["type", str],
            ["side", str],
            ["status", str]
        ]
        if self.__exchange_name == "coinbase_pro":
            """
            [
                {
                    "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                    "price": "0.10000000",
                    "size": "0.01000000",
                    "product_id": "BTC-USD",
                    "side": "buy",
                    "stp": "dc",
                    "type": "limit",
                    "time_in_force": "GTC",
                    "post_only": false,
                    "created_at": "2016-12-08T20:02:28.53864Z",
                    "fill_fees": "0.0000000000000000",
                    "filled_size": "0.00000000",
                    "executed_value": "0.0000000000000000",
                    "status": "open",
                    "settled": false
                },
                {
                    ...
                }
            ]
            """
            if not self.__paper_trading:
                if product_id is None:
                    orders = list(self.__calls.get_orders())
                else:
                    orders = list(self.__calls.get_orders(product_id, kwargs=kwargs))

                if orders[0] == 'message':
                    raise InvalidOrder("Invalid Order: " + str(orders))

                for i in range(len(orders)):
                    orders[i] = utils.isolate_specific(needed, orders[i])

                return orders
            else:
                open_orders = []
                for i in self.__paper_trade_orders:
                    if i["status"] == "open":
                        open_orders.append(i)

                return open_orders
        elif self.__exchange_name == "binance":
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
            if product_id is not None:
                product_id = utils.to_exchange_coin_id(product_id, "binance")
                orders = self.__calls.get_open_orders(symbol=product_id)
            else:
                orders = self.__calls.get_open_orders()
            renames = [
                ["orderId", "id"],
                ["origQty", "size"],
                ["isWorking", "status"]
            ]
            for i in range(len(orders)):
                orders[i] = utils.rename_to(renames, orders[i])
                orders[i] = utils.isolate_specific(needed, orders[i])

            return orders

    def get_order(self, currency_id, order_id) -> dict:
        needed = [
            ["id", str],
            ["product_id", str],
            ["price", float],
            ["size", float],
            ["type", str],
            ["side", str],
            ["status", str],
            ["funds", float]
        ]
        if self.__exchange_name == "coinbase_pro":
            """
            {
                "created_at": "2017-06-18T00:27:42.920136Z",
                "executed_value": "0.0000000000000000",
                "fill_fees": "0.0000000000000000",
                "filled_size": "0.00000000",
                "id": "9456f388-67a9-4316-bad1-330c5353804f",
                "post_only": true,
                "price": "1.00000000",
                "product_id": "BTC-USD",
                "settled": false,
                "side": "buy",
                "size": "1.00000000",
                "status": "pending",
                "stp": "dc",
                "time_in_force": "GTC",
                "type": "limit"
            }
            This is the response for a market order
            {
                'id': '8d3a6ea5-8d6d-4486-9c98-b266bae9a67c', 
                'side': 'buy', 
                'type': 'market', 
                'status': 'done',
                'product_id': 'BTC-USD',
                'profile_id': '4107a8cc-9fee-4ed4-b609-d87011675ed5',
                'funds': '39.9201596800000000', 
                'specified_funds': '40.0000000000000000',
                'post_only': False, 
                'created_at': '2021-05-14T18:03:43.292914Z',
                'done_at': '2021-05-14T18:03:43.297Z', 
                'done_reason': 'filled',
                'fill_fees': '0.0798400768200000', 
                'filled_size': '0.00078825',
                'executed_value': '39.9200384100000000', 
                'settled': True
            }
            """
            if not self.__paper_trading:
                response = self.__calls.get_order(order_id)
                return utils.isolate_specific(needed, response)
            else:
                for i in self.__paper_trade_orders:
                    if i["id"] == order_id:
                        return i

        elif self.__exchange_name == "binance":
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
                ["isWorking", "status"]
            ]
            response = self.__calls.get_order(symbol=currency_id, orderId=int(order_id))
            response = utils.rename_to(renames, response)
            return utils.isolate_specific(needed, response)

    """
    Coinbase Pro: get_fees
    Binance: get_trade_fee
    """
    def get_fees(self):
        needed = [
            ['maker_fee_rate', float],
            ['taker_fee_rate', float]
        ]
        if self.__exchange_name == "coinbase_pro":
            """
            {
                'maker_fee_rate': '0.0050',
                'taker_fee_rate': '0.0050',
                'usd_volume': '37.69'
            }
            """
            fees = self.__calls.get_fees()
            return utils.isolate_specific(needed, fees)
        elif self.__exchange_name == "binance":
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
            account = self.__calls.get_account()
            # Get rid of the stuff we really don't need this time
            account.pop('canTrade')
            account.pop('canWithdraw')
            account.pop('canDeposit')
            account.pop('balances')
            # Rename makers and takers
            account['maker_fee_rate'] = account.pop('makerCommission')/100
            account['taker_fee_rate'] = account.pop('takerCommission')/100
            # Isolate
            return utils.isolate_specific(needed, account)

    """
    Coinbase Pro: get_account_history
    Binance: 
        get_deposit_history
        get_withdraw_history
        
    """
    def get_product_history(self, product_id, epoch_start, epoch_stop, granularity):
        """
        Returns the product history from an exchange
        Args:
            product_id: Blankly product ID format (BTC-USD)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            granularity: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
        """
        # Hope nobody is fixing this in the year 5138 at 9:46:40 AM (GMT)
        if epoch_start > 100000000000:
            epoch_start = int(epoch_start / 1000)
        if epoch_stop > 100000000000:
            epoch_stop = int(epoch_stop / 1000)

        if self.__exchange_name == "coinbase_pro":
            accepted_grans = [60, 300, 900, 3600, 21600, 86400]
            if granularity not in accepted_grans:
                warnings.warn("Granularity is not an accepted granularity...rounding to nearest valid value.")
                granularity = accepted_grans[min(range(len(accepted_grans)),
                                                 key=lambda i: abs(accepted_grans[i]-granularity))]

            # Figure out how many points are needed
            need = int((epoch_stop - epoch_start) / granularity)
            window_open = epoch_start
            history = []
            # Iterate while its more than max
            while need > 300:
                # Close is always 300 points ahead
                window_close = window_open + 300 * granularity
                open_iso = utils.ISO8601_from_epoch(window_open)
                close_iso = utils.ISO8601_from_epoch(window_close)
                history = history + self.__calls.get_product_historic_rates(product_id, open_iso, close_iso,
                                                                            granularity)

                window_open = window_close
                need -= 300
                time.sleep(1)

            # Fill the remainder
            open_iso = utils.ISO8601_from_epoch(window_open)
            close_iso = utils.ISO8601_from_epoch(epoch_stop)
            history_block = history + self.__calls.get_product_historic_rates(product_id, open_iso, close_iso,
                                                                              granularity)
            history_block.sort(key=lambda x: x[0])
            return pd.DataFrame(history_block, columns=['time', 'low', 'high', 'open', 'close', 'volume'])

        elif self.__exchange_name == "binance":
            accepted_grans = [60, 180, 300, 900, 1800, 3600, 7200, 14400,
                              21600, 28800, 43200, 86400, 259200, 604800, 2592000]
            if granularity not in accepted_grans:
                warnings.warn("Granularity is not an accepted granularity...rounding to nearest valid value.")
                granularity = accepted_grans[min(range(len(accepted_grans)),
                                                 key=lambda i: abs(accepted_grans[i]-granularity))]
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
            gran_string = lookup_dict[granularity]

            # Figure out how many points are needed
            need = int((epoch_stop - epoch_start) / granularity)
            window_open = epoch_start
            history = []

            # Convert coin id to binance coin
            product_id = utils.to_exchange_coin_id(product_id, 'binance')
            while need > 1000:
                # Close is always 300 points ahead
                window_close = window_open + 1000 * granularity
                history = history + self.__calls.get_klines(symbol=product_id, startTime=window_open*1000,
                                                            endTime=window_close*1000, interval=gran_string, limit=1000)

                window_open = window_close
                need -= 1000
                time.sleep(1)

            # Fill the remainder
            history_block = history + self.__calls.get_klines(symbol=product_id, startTime=window_open*1000,
                                                              endTime=epoch_stop*1000, interval=gran_string, limit=1000)

            data_frame = pd.DataFrame(history_block, columns=['time', 'open', 'high', 'low', 'close', 'volume',
                                                              'close time', 'quote asset volume', 'number of trades',
                                                              'taker buy base asset volume',
                                                              'taker buy quote asset volume', 'ignore'])
            # Clear the ignore column, why is that there binance?
            del data_frame['ignore']
            # Want them in this order: ['time (epoch)', 'low', 'high', 'open', 'close', 'volume']

            return data_frame.reindex(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    """
    Coinbase Pro: Get Currencies
    Binance: get_products
    """
    def get_market_limits(self, product_id):
        needed = [
            ["market", str],
            ["base_currency", str],
            ["quote_currency", str],
            ["base_min_size", float],  # Minimum size to buy
            ["base_max_size", float],  # Maximum size to buy
            ["quote_increment", float],  # Specifies the min order price as well as the price increment.
            ["base_increment", float],  # Specifies the minimum increment for the base_currency.
            ["max_orders", int],
            ["min_price", float],
            ["max_price", float]
        ]
        if self.__exchange_name == "coinbase_pro":
            renames = [
                ["id", "market"]
            ]
            """
            Returns:
            list: List of available currency pairs. Example::
                [
                    {
                        "id": "BTC-USD",
                        "display_name": "BTC/USD",
                        "base_currency": "BTC",
                        "quote_currency": "USD",
                        "base_increment": "0.00000001",
                        "quote_increment": "0.01000000",
                        "base_min_size": "0.00100000",
                        "base_max_size": "280.00000000",
                        "min_market_funds": "5",
                        "max_market_funds": "1000000",
                        "status": "online",
                        "status_message": "",
                        "cancel_only": false,
                        "limit_only": false,
                        "post_only": false,
                        "trading_disabled": false
                    },
                    ...
                ]
                """
            response = self.__calls.get_products()
            products = None
            for i in response:
                if i["id"] == product_id:
                    products = i

            if products is None:
                raise ValueError("Specified market not found")

            products = utils.rename_to(renames, products)
            products["min_price"] = 0
            # These don't really exist on this exchange
            products["max_price"] = -1
            products["max_orders"] = -1
            return utils.isolate_specific(needed, products)
        elif self.__exchange_name == "binance":
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
            symbol_data = self.__calls.get_exchange_info()["symbols"]
            for i in symbol_data:
                if i["symbol"] == converted_symbol:
                    symbol_data = i
                    current_price = float(self.__calls.get_avg_price(symbol=converted_symbol)['price'])
                    break
            if current_price is None:
                raise ValueError("Specified market not found")

            filters = symbol_data["filters"]
            hard_min_price = float(filters[0]["minPrice"])
            hard_max_price = float(filters[0]["maxPrice"])
            quote_increment = float(filters[0]["tickSize"])

            percent_min_price = float(filters[1]["multiplierUp"]) * current_price
            percent_max_price = float(filters[1]["multiplierDown"]) * current_price

            min_quantity = float(filters[2]["minQty"])
            max_quantity = float(filters[2]["maxQty"])
            base_increment = float(filters[2]["stepSize"])

            max_orders = int(filters[6]["maxNumOrders"])

            if hard_min_price < percent_min_price:
                min_price = percent_min_price
            else:
                min_price = hard_min_price

            if hard_max_price > percent_max_price:
                max_price = percent_max_price
            else:
                max_price = hard_max_price

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
            }

    def get_price(self, currency_pair) -> float:
        """
        Returns just the price of a currency pair.
        """
        if self.__exchange_name == "coinbase_pro":
            """
            {
                'trade_id': 28976297, 
                'price': '57579.72', 
                'size': '0.00017367', 
                'time': '2021-05-01T17:01:32.717482Z', 
                'bid': '57579.72', 
                'ask': '57579.74', 
                'volume': '31137.51184419'
            }
            """
            response = self.__calls.get_product_ticker(currency_pair)
            return float(response['price'])
        elif self.__exchange_name == "binance":
            currency_pair = utils.to_exchange_coin_id(currency_pair, "binance")
            response = self.__calls.get_symbol_ticker(symbol=currency_pair)
            return float(response['price'])
