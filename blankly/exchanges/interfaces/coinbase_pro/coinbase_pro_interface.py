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

import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder


class CoinbaseProInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_API):
        super().__init__(exchange_name, authenticated_API, valid_resolutions=[60, 300, 900, 3600, 21600, 86400])

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
        self.__exchange_properties = {
            "maker_fee_rate": fees['maker_fee_rate'],
            "taker_fee_rate": fees['taker_fee_rate']
        }

    def get_products(self):
        needed = self.needed['get_products']
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
            products[i]["symbol"] = products[i].pop("id")
            products[i]["base_asset"] = products[i].pop("base_currency")
            products[i]["quote_asset"] = products[i].pop("quote_currency")
            products[i] = utils.isolate_specific(needed, products[i])
        return products

    def get_account(self, symbol=None) -> utils.AttributeDict:
        """
        Get all currencies in an account, or sort by symbol/account_id
        Args:
            symbol (Optional): Filter by particular symbol

            These arguments are mutually exclusive
        Coinbase Pro: get_account
        """
        symbol = super().get_account(symbol=symbol)

        needed = self.needed['get_account']
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
        accounts = self.calls.get_accounts()

        parsed_dictionary = utils.AttributeDict({})

        # We have to sort through it if the accounts are none
        if symbol is not None:
            for i in accounts:
                if i["currency"] == symbol:
                    parsed_value = utils.isolate_specific(needed, i)
                    dictionary = utils.AttributeDict({
                        'available': parsed_value['available'],
                        'hold': parsed_value['hold']
                    })
                    return dictionary
            raise ValueError("Symbol not found")
        for i in range(len(accounts)):
            parsed_dictionary[accounts[i]['currency']] = utils.AttributeDict({
                'available': float(accounts[i]['available']),
                'hold': float(accounts[i]['hold'])
            })

        return parsed_dictionary

    def market_order(self, symbol, side, funds) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            symbol: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
        """
        needed = self.needed['market_order']
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
            'symbol': symbol,
            'type': 'market'
        }
        response = self.calls.place_market_order(symbol, side, funds=funds)
        if "message" in response:
            raise InvalidOrder("Invalid Order: " + response["message"])
        response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
        response["symbol"] = response.pop('product_id')
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
            'symbol': product_id,
            'type': 'limit'
        }
        response = self.calls.place_limit_order(product_id, side, price, size=size)
        if "message" in response:
            raise InvalidOrder("Invalid Order: " + response["message"])
        response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])
        response["symbol"] = response.pop('product_id')
        response = utils.isolate_specific(needed, response)
        return LimitOrder(order, response, self)

    """
    Stop limit isn't added to the abstract class because the binance version is barely supported.
    
    If you want to use this function you can, just do interface.stop_limit(args) if you're using a coinbase pro 
    interface
    """

    def stop_limit(self, symbol, side, stop_price, limit_price, size, stop='loss') -> StopLimit:
        """
        Used for placing stop orders
        Args:
            symbol (str): currency to buy
            side (str): buy/sell
            stop_price (float): Price to trigger the stop order at
            limit_price (float): Price to set the stop limit
            size (float): Amount of base currency to buy: (1.3 BTC)
            stop (str) (optional): Stop type of "loss" or "entry"

        {
            'id': '3a98a5c6-05a0-4e46-b8e4-3f27358fe27d',
            'price': '29500',
            'size': '0.01',
            'product_id':
            'BTC-USD',
            'side': 'buy',
            'stp': 'dc',
            'type': 'limit',
            'time_in_force':
            'GTC',
            'post_only': False,
            'created_at': '2021-05-28T19:24:52.010449Z',
            'stop': 'loss',
            'stop_price': '30000',
            'fill_fees': '0',
            'filled_size': '0',
            'executed_value': '0',
            'status': 'pending',
            'settled': False
        }
        """
        order = {
            'symbol': symbol,
            'side': side,
            'type': 'stop',
            'stop': stop,
            'stop_price': stop_price,
            'size': size,
            'price': limit_price
        }
        response = self.calls.place_order(product_id=symbol,
                                          order_type='limit',
                                          side=side,
                                          stop=stop,  # loss
                                          stop_price=stop_price,
                                          size=size,
                                          price=limit_price
                                          )
        response['limit_price'] = response.pop('price')
        response["symbol"] = response.pop('product_id')
        return StopLimit(order, response, self)

    def cancel_order(self, symbol, order_id) -> dict:
        """
        Returns:
            dict: Containing the order_id of cancelled order. Example::
            { "order_id": "c5ab5eae-76be-480e-8961-00792dc7e138" }
        """
        return {"order_id": self.calls.cancel_order(order_id)}

    def get_open_orders(self, symbol=None):
        """
        List open orders.
        """
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
        if symbol is None:
            orders = list(self.calls.get_orders())
        else:
            orders = list(self.calls.get_orders(product_id=symbol))

        if len(orders) == 0:
            return []
        if orders[0] == 'message':
            raise InvalidOrder("Invalid Order: " + str(orders))

        for i in range(len(orders)):
            orders[i]["created_at"] = utils.epoch_from_ISO8601(orders[i]["created_at"])
            needed = self.choose_order_specificity(orders[i]['type'])
            orders[i]["symbol"] = orders[i].pop('product_id')
            orders[i] = utils.isolate_specific(needed, orders[i])

        return orders

    def get_order(self, symbol, order_id) -> dict:
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
        response = self.calls.get_order(order_id)
        if 'message' in response:
            # This part will run through all orders if the user enables the setting
            # Leaving this commented because its useful in getting all orders if we add that
            # if self.user_preferences['settings']['coinbase_pro']['search_all_fills']:
            #     all_orders = list(self.calls.get_orders(product_id=currency_id, status='all'))
            #     found = False
            #     for i in all_orders:
            #         if i['id'] == order_id:
            #             found = True
            #             response = i
            #
            #     if not found:
            #         raise APIException("Invalid: " + str(response['message']) + ", was the order canceled?")
            # else:
            raise APIException("Invalid: " + str(response['message']) + ", was the order canceled?")
        response["created_at"] = utils.epoch_from_ISO8601(response["created_at"])

        if response['type'] == 'market':
            needed = self.needed['market_order']
        elif response['type'] == 'limit':
            needed = self.needed['limit_order']
        else:
            needed = self.needed['market_order']

        response["symbol"] = response.pop('product_id')
        return utils.isolate_specific(needed, response)

    """
    Coinbase Pro: get_fees
    binance: get_trade_fee
    """

    def get_fees(self) -> dict:
        needed = self.needed['get_fees']
        """
        {
            'maker_fee_rate': '0.0050',
            'taker_fee_rate': '0.0050',
            'usd_volume': '37.69'
        }
        """
        fees = self.calls.get_fees()
        return utils.isolate_specific(needed, fees)

    """
    Coinbase Pro: get_account_history
    binance: 
        get_deposit_history
        get_withdraw_history

    """

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
        # Iterate while its more than max
        while need > 300:
            # Close is always 300 points ahead
            window_close = window_open + 300 * resolution
            open_iso = utils.ISO8601_from_epoch(window_open)
            close_iso = utils.ISO8601_from_epoch(window_close)
            response = self.calls.get_product_historic_rates(symbol, open_iso, close_iso, resolution)
            if isinstance(response, dict):
                raise APIException(response['message'])
            history = history + response

            window_open = window_close
            need -= 300
            time.sleep(.2)
            utils.update_progress((initial_need - need) / initial_need)

        # Fill the remainder
        open_iso = utils.ISO8601_from_epoch(window_open)
        close_iso = utils.ISO8601_from_epoch(epoch_stop)
        response = self.calls.get_product_historic_rates(symbol, open_iso, close_iso, resolution)
        if isinstance(response, dict):
            raise APIException(response['message'])
        history_block = history + response
        history_block.sort(key=lambda x: x[0])

        df = pd.DataFrame(history_block, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        # df[['time']] = df[['time']].astype(int)
        # Have to cast this for some reason
        df[['low', 'high', 'open', 'close', 'volume']] = df[['low', 'high', 'open', 'close', 'volume']].astype(float)

        return df

    """
    Coinbase Pro: Get Currencies
    binance: get_products
    """

    def get_order_filter(self, symbol: str):
        """
        Returns:
        list: List of available currency pairs. Example::
            [
                {
                    "id": "BTC-USD",  <-- Needed
                    "display_name": "BTC/USD",
                    "base_currency": "BTC", <-- Needed
                    "quote_currency": "USD",  <-- Needed
                    "base_increment": "0.00000001",  <-- Needed
                    "quote_increment": "0.01000000",  <-- Needed
                    "base_min_size": "0.00100000",  <-- Needed
                    "base_max_size": "280.00000000",  <-- Needed
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
        response = self.calls.get_products()
        products = None
        for i in response:
            if i["id"] == symbol:
                products = i
                break

        if products is None:
            raise LookupError("Specified market not found")

        return {
            "symbol": products.pop('id'),
            "base_asset": products.pop('base_currency'),
            "quote_asset": products.pop('quote_currency'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": float(products.pop('base_min_size')),  # Minimum size to buy
                "base_max_size": float(products.pop('base_max_size')),  # Maximum size to buy
                "base_increment": float(products.pop('base_increment')),  # Specifies the minimum increment
                # for the base_asset.
                "price_increment": float(products['quote_increment']),

                "min_price": float(products['quote_increment']),
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,
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
        """
        Returns just the price of a currency pair.
        """
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
        response = self.calls.get_product_ticker(symbol)
        if 'message' in response:
            raise APIException("Error: " + response['message'])
        return float(response['price'])
