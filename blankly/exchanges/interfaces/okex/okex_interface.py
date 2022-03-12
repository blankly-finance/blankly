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
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 180, 300, 900, 1800, 3600,
                                                                              7200, 14400, 21600, 43200, 86400, 604800])

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
            products[i]["symbol"] = products[i].pop("instrument_id")
            products[i]["base_asset"] = products[i].pop("base_currency")
            products[i]["quote_asset"] = products[i].pop("quote_currency")
            products[i]["base_min_size"] = products[i].pop("min_size")
            products[i]["base_max_size"] = 100000000  # This value was hardcoded
            products[i]["base_increment"] = products[i].pop("size_increment")
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

        response = self.calls.take_order(symbol, side, size=size, price=price)
        if "message" in response:
            raise InvalidOrder("Invalid Order: " + response["message"])

        response_details = self.calls.get_order_info(symbol, order_id=response['order_id'])

        response_details["created_at"] = time.time()
        response_details["id"] = response_details.pop('order_id')
        response_details["status"] = response_details.pop('result')
        response_details = utils.isolate_specific(needed, response_details)
        return LimitOrder(order, response_details, self)


    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        Returns:
            dict: Containing the order_id of cancelled order. Example::
            { "client_oid": "order123", }
        """
        return {"order_id": self.calls.revoke_order(symbol)}

    def get_open_orders(self, symbol: str):
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
            raise ValueError("There was no symbol inputted, please try again.")
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

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        pass
    #
    #     resolution = blankly.time_builder.time_interval_to_seconds(resolution)
    #     iso_start = utils.iso8601_from_epoch(epoch_start)
    #     iso_stop =  utils.iso8601_from_epoch(epoch_stop)
    #
    #     accepted_grans = [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 604800]
    #
    #     if resolution not in accepted_grans:
    #         utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
    #         resolution = accepted_grans[min(range(len(accepted_grans)),
    #                                         key=lambda i: abs(accepted_grans[i] - resolution))]
    #     resolution = int(resolution)
    #
    #     need = int((epoch_stop - epoch_start) / resolution)
    #     initial_need = need
    #     window_open = epoch_start
    #     history = []
    #     # Iterate while its more than max
    #     while need > 300:
    #         # Close is always 300 points ahead
    #         window_close = window_open + 300 * resolution
    #         open_iso = utils.iso8601_from_epoch(window_open)
    #         close_iso = utils.iso8601_from_epoch(window_close)
    #         response = self.calls.get_product_historic_rates(symbol, open_iso, close_iso, resolution)
    #         if isinstance(response, dict):
    #             raise APIException(response['message'])
    #         history = history + response
    #
    #         window_open = window_close
    #         need -= 300
    #         time.sleep(.2)
    #         utils.update_progress((initial_need - need) / initial_need)
    #
    #     # Fill the remainder
    #     open_iso = utils.iso8601_from_epoch(window_open)
    #     close_iso = utils.iso8601_from_epoch(epoch_stop)
    #     response = self.calls.get_product_historic_rates(symbol, open_iso, close_iso, resolution)
    #     if isinstance(response, dict):
    #         raise APIException(response['message'])
    #     history_block = history + response
    #     history_block.sort(key=lambda x: x[0])
    #
    #     df = pd.DataFrame(history_block, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    #     # df[['time']] = df[['time']].astype(int)
    #     # Have to cast this for some reason
    #     df[['time']] = df[['time']].astype(int)
    #     df[['low', 'high', 'open', 'close', 'volume']] = df[['low', 'high', 'open', 'close', 'volume']].astype(float)
    #
    #     return df

    def get_order_filter(self, symbol: str) -> dict:
        response = self.calls.get_coin_info()
        products = None
        for i in response:
            if i["id"] == symbol:
                products = i
                break

        base_min_size = float(products.pop('min_size'))
        # base_max_size = 100000000   #This value was hardcoded
        base_increment = float(products.pop('size_increment'))

        return {
            "symbol": products.pop('instrument_id'),
            "base_asset": products.pop('base_currency'),
            "quote_asset": products.pop('quote_currency'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": 100000000,  # Maximum size to buy, this value was hardcoded
                "base_increment": base_increment,  # Specifies the minimum increment
                # for the base_asset.
                "price_increment": float(products['tick_size']),

                "min_price": float(products['tick_size']),
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,

                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": 100000000,  # Maximum size to buy, this value was hardcoded
                "base_increment": base_increment,  # Specifies the minimum increment

                "quote_increment": float(products.pop('tick_size')),  # Specifies the min order price as well
                # as the price increment.
                "buy": {
                    "min_funds": 0.1,  # This value was hardcoded
                    "max_funds": 1000000,  # This value was hardcoded
                },
                "sell": {
                    "min_funds": 0.1,  # This value was hardcoded
                    "max_funds": 1000000,  # This value was hardcoded
                },
            },
            "exchange_specific": {**products}
        }

    def get_price(self, symbol) -> float:
        """
        Returns just the price of a currency pair.
        """
        response = self.get_specific_ticker(symbol)
        if 'message' in response:
            raise APIException("Error: " + response['message'])
        return float(response['last'])
