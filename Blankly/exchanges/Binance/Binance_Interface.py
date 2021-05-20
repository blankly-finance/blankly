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
import pandas as pd
import Blankly.utils.utils as utils
from Blankly.utils.purchases.limit_order import LimitOrder
from Blankly.utils.purchases.market_order import MarketOrder
from Blankly.interface.currency_Interface import CurrencyInterface


class BinanceInterface(CurrencyInterface):
    def __init__(self, exchange_name, authenticated_API):
        super().__init__(exchange_name, authenticated_API)

    def init_exchange(self):
        if self.exchange_name == "coinbase_pro":
            fees = self.calls.get_fees()
            try:
                if fees['message'] == "Invalid API Key":
                    raise LookupError("Invalid API Key - are you trying to use your normal exchange keys "
                                      "while in sandbox mode?")
            except KeyError:
                pass
            self.__exchange_properties = {
                "maker_fee_rate": fees['maker_fee_rate'],
                "taker_fee_rate": fees['taker_fee_rate']
            }
        if self.exchange_name == "binance":
            account = self.calls.get_account()
            self.__exchange_properties = {
                "maker_fee_rate": account['makerCommission'] / 100,
                "taker_fee_rate": account['takerCommission'] / 100,
                "buyer_fee_rate": account['buyerCommission'] / 100,  # I'm not sure of the case when these are nonzero
                "seller_fee_rate": account['sellerCommission'] / 100,
            }
            symbols = self.calls.get_exchange_info()["symbols"]
            base_assets = []
            for i in symbols:
                base_assets.append(i["baseAsset"])
            self.__available_currencies = base_assets

    def get_products(self):
        needed = [["currency_id", str],
                  ["base_currency", str],
                  ["quote_currency", str],
                  ["base_min_size", float],
                  ["base_max_size", float],
                  ["base_increment", float]]
        if self.exchange_name == "coinbase_pro":
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
            products = self.calls.get_products()
            for i in range(len(products)):
                # Rename needed
                products[i]["currency_id"] = products[i].pop("id")
                # Isolate unimportant
                products[i] = utils.isolate_specific(needed, products[i])
            return products
        elif self.exchange_name == "binance":
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
                return utils.isolate_specific(needed, products[i])
            return products

    def get_account(self, currency=None, override_paper_trading=False):
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency (Optional): Filter by particular currency
            override_paper_trading (Optional bool): If paper trading is enabled, setting this to true will get the
             actual account values

            These arguments are mutually exclusive
        Coinbase Pro: get_account
        Binance: get_account["balances"]
        """
        currency, internal_paper_trade = super().get_account(currency=currency, override_paper_trading=override_paper_trading)

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
                raise LookupError("Currency not found")

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
        response = self.calls.order_market(symbol=modified_product_id, side=side, quoteOrderQty=funds)
        response = utils.rename_to(renames, response)
        response = utils.isolate_specific(needed, response)
        response["transactTime"] = response["transactTime"] / 1000
        return MarketOrder(order, response, self)

    def limit_order(self, product_id, side, price, size) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
            kwargs: specific arguments that may be used by each exchange, (if exchange is known)
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
        response = self.calls.cancel_order(symbol=currency_id, orderId=order_id)
        response = utils.rename_to(renames, response)
        return utils.isolate_specific(needed, response)

    def get_open_orders(self, product_id=None):
        """
        List open orders.
        """
        needed = self.needed['get_open_orders']
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
            orders = self.calls.get_open_orders()
        else:
            orders = self.calls.get_open_orders()
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
        needed = self.needed['get_order']
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
        response = self.calls.get_order(symbol=currency_id, orderId=int(order_id))
        response = utils.rename_to(renames, response)
        return utils.isolate_specific(needed, response)

    """
    Coinbase Pro: get_fees
    Binance: get_trade_fee
    """

    def get_fees(self):
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
        epoch_start, epoch_stop = super().get_product_history(product_id, epoch_start, epoch_stop, granularity)

        epoch_start = int(epoch_start)
        epoch_stop = int(epoch_stop)

        accepted_grans = [60, 180, 300, 900, 1800, 3600, 7200, 14400,
                          21600, 28800, 43200, 86400, 259200, 604800, 2592000]
        if granularity not in accepted_grans:
            warnings.warn("Granularity is not an accepted granularity...rounding to nearest valid value.")
            granularity = accepted_grans[min(range(len(accepted_grans)),
                                             key=lambda i: abs(accepted_grans[i] - granularity))]
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
            history = history + self.calls.get_klines(symbol=product_id, startTime=window_open * 1000,
                                                      endTime=window_close * 1000, interval=gran_string,
                                                      limit=1000)

            window_open = window_close
            need -= 1000
            time.sleep(1)

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

        return data_frame.reindex(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    """
    Coinbase Pro: Get Currencies
    Binance: get_products
    """

    def get_market_limits(self, product_id):
        needed = self.needed['get_market_limits']
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
        currency_pair = utils.to_exchange_coin_id(currency_pair, "binance")
        response = self.calls.get_symbol_ticker(symbol=currency_pair)
        return float(response['price'])
