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
import Blankly.utils
from Blankly.Purchase import Purchase


class APIInterface:
    def __init__(self, exchange_name, authenticated_API):
        self.__exchange_name = exchange_name
        self.__calls = authenticated_API
        self.__ticker_manager = None
        # Reload user preferences here
        self.__user_preferences = Blankly.utils.load_user_preferences()
        self.__paper_trading = self.__user_preferences["settings"]["paper_trade"]
        # TODO, improve creation of its own properties
        self.__exchange_properties = None
        # Some exchanges like binance will not return a value of 0.00 if there is no balance
        self.__available_currencies = {}
        self.__init_exchange__()

    def __init_exchange__(self):
        if self.__exchange_name == "coinbase_pro":
            fees = self.__calls.get_fees()
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

    @staticmethod
    def __rename_to(keys_array, renaming_dictionary):
        """
        Args:
            keys_array: A two dimensional array that contains information on which keys are changed:
                keys_array = [
                    ["key1", "new name"],
                    ["id", "user_id"],
                    ["frankie", "gerald"],
                ]
            renaming_dictionary: Dictionary to perform the renaming on
        """
        renaming_dictionary["exchange_specific"] = {}
        for i in keys_array:
            try:
                # Check if it has the new name
                error_test = renaming_dictionary[i[1]]
                # If we're here this key has already been defined, push it to the specific
                renaming_dictionary["exchange_specific"][i[1]] = renaming_dictionary.pop(i[1])
            except KeyError:
                pass
            renaming_dictionary[i[1]] = renaming_dictionary.pop(i[0])
        return renaming_dictionary

    # Non-recursive check
    @staticmethod
    def __isolate_specific(needed, compare_dictionary):
        """
        This is the parsing algorithm used to homogenize the dictionaries
        """
        # Create a column vector for the keys
        column = [column[0] for column in needed]
        # Create an area to hold the specific data
        exchange_specific = {}
        required = False
        for k, v in compare_dictionary.items():
            # Check if the value is one of the keys
            for index, val in enumerate(column):
                required = False
                # If it is, there is a state value for it
                if k == val:
                    # Push type to value
                    compare_dictionary[k] = needed[index][1](v)
                    required = True
                    break
            # Must not be found
            # Append non-necessary to the exchange specific dict
            # There has to be a way to do this without raising a flag value
            if not required:
                exchange_specific[k] = compare_dictionary[k]

        # If there exists the exchange specific dict in the compare dictionary
        # This is done because after renaming, if there are naming conflicts they will already have been pushed here,
        # generally the "else" should always be what runs.
        if "exchange_specific" not in compare_dictionary:
            # If there isn't, just add it directly
            compare_dictionary["exchange_specific"] = exchange_specific
        else:
            # If there is, pull them together
            compare_dictionary["exchange_specific"] = {**compare_dictionary["exchange_specific"], **exchange_specific}
        # Pull the specific keys out
        for k, v in exchange_specific.items():
            del compare_dictionary[k]
        return compare_dictionary

    def append_ticker_manager(self, ticker_manager):
        self.__ticker_manager = ticker_manager

    def get_calls(self):
        """
        Returns:
             The exchange's direct calls object. A Blankly Bot class should have immediate access to this by
             default
        """
        return self.__calls

    def get_products(self, product_id=None):
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
                return self.__isolate_specific(needed, products[i])
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
                return self.__isolate_specific(needed, products[i])
            return products

    def get_account(self, currency=None, account_id=None):
        """
        Get all currencies in an account, or sort by currency/account_id
        Coinbase Pro: get_account
        Binance: get_account["balances"]
        """
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
                            parsed_value = self.__isolate_specific(needed, i)
                            return parsed_value
                    warnings.warn("Currency not found")
                for i in range(len(accounts)):
                    accounts[i] = self.__isolate_specific(needed, accounts[i])
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
                return self.__calls.get_account(account_id)
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
                            accounts = self.__rename_to(renames, accounts)
                            parsed_value = self.__isolate_specific(needed, accounts[i])
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
                        accounts = self.__rename_to(renames, accounts)
                        accounts[index] = self.__isolate_specific(needed, accounts[index])
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

    def market_order(self, product_id, side, funds, **kwargs):
        """
        Used for buying or selling market orders
        Args:
            product_id: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
            kwargs: specific arguments that may be used by each exchange, if exchange is known
        """
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
                'funds': funds,
                'side': side,
                'product_id': product_id,
                'type': 'market'
            }
            response = self.__calls.place_market_order(product_id, side, funds, kwargs=kwargs)
            return Purchase(order,
                            response,
                            self.__ticker_manager.get_ticker(product_id, override_default_exchange_name="coinbase_pro"),
                            self.__exchange_properties)

    def limit_order(self, product_id, side, price, size, **kwargs):
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
            kwargs: specific arguments that may be used by each exchange, (if exchange is known)
        """
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
                'product_id': product_id,
                'type': 'limit'
            }
            self.__calls.placeOrder(product_id, side, price, size)
            response = self.__calls.place_market_order(product_id, side, price, size, kwargs=kwargs)
            return Purchase(order,
                            response,
                            self.__ticker_manager.get_ticker(product_id, override_default_exchange_name="coinbase_pro"),
                            self.__exchange_properties)

    def stop_order(self, product_id, side, price, size, **kwargs):
        """
        Used for placing stop orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
            kwargs: specific arguments that may be used by each exchange, (if exchange is known)
        """
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
                'product_id': product_id,
                'type': 'stop'
            }
            self.__calls.placeOrder(product_id, side, price, size)
            response = self.__calls.place_market_order(product_id, side, price, size, kwargs=kwargs)
            return Purchase(order,
                            response,
                            self.__ticker_manager.get_ticker(product_id,
                                                             override_default_exchange_name="coinbase_pro"),
                            self.__exchange_properties)

    def cancel_order(self, order_id):
        if self.__exchange_name == "coinbase_pro":
            """
            [ "c5ab5eae-76be-480e-8961-00792dc7e138" ]
            """
            return self.__calls.cancel_order(order_id)

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
            ["open", bool]
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
            if product_id is None:
                orders = list(self.__calls.get_orders(kwargs=kwargs))
            else:
                orders = list(self.__calls.get_orders(product_id, kwargs=kwargs))

            for i in range(len(orders)):
                orders[i] = self.__isolate_specific(needed, orders[i])

            return orders
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
                product_id = Blankly.utils.to_exchange_coin_id(product_id, "binance")
                orders = self.__calls.get_open_orders(symbol=product_id)
            else:
                orders = self.__calls.get_open_orders()
            renames = [
                ["orderId", "id"],
                ["origQty", "size"],
                ["isWorking", "status"]
            ]
            for i in range(len(orders)):
                orders[i] = self.__rename_to(renames, orders[i])
                orders[i] = self.__isolate_specific(needed, orders[i])

            return orders

    def get_order(self, order_id):
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
            """
            return self.__calls.get_order(order_id)

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
            return self.__isolate_specific(needed, fees)
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
            return self.__isolate_specific(needed, account)

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
                open_iso = Blankly.utils.ISO8601_from_epoch(window_open)
                close_iso = Blankly.utils.ISO8601_from_epoch(window_close)
                history = history + self.__calls.get_product_historic_rates(product_id, open_iso, close_iso,
                                                                            granularity)

                window_open = window_close
                need -= 300
                time.sleep(1)

            # Fill the remainder
            open_iso = Blankly.utils.ISO8601_from_epoch(window_open)
            close_iso = Blankly.utils.ISO8601_from_epoch(epoch_stop)
            history_block = history + self.__calls.get_product_historic_rates(product_id, open_iso, close_iso,
                                                                              granularity)
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
            product_id = Blankly.utils.to_exchange_coin_id(product_id, 'binance')
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

    def get_latest_trades(self, product_id, **kwargs):
        if self.__exchange_name == "coinbase_pro":
            # De-paginate
            """
            [{
                 "time": "2014-11-07T22:19:28.578544Z",
                 "trade_id": 74,
                 "price": "10.00000000",
                 "size": "0.01000000",
                 "side": "buy"
             }, {
                 "time": "2014-11-07T01:08:43.642366Z",
                 "trade_id": 73,
                 "price": "100.00000000",
                 "size": "0.01000000",
                 "side": "sell"
            }]
            """
            return list(self.__calls.get_product_trades(product_id, kwargs=kwargs))

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

            products = self.__rename_to(renames, products)
            products["min_price"] = 0
            # These don't really exist on this exchange
            products["max_price"] = -1
            products["max_orders"] = -1
            return self.__isolate_specific(needed, products)
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

            converted_symbol = Blankly.utils.to_exchange_coin_id(product_id, 'binance')
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
