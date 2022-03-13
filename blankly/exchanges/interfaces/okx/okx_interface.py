import time
import pandas as pd
import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.okx.okx_api import Client as OkxAPI, MarketAPI, AccountAPI, TradeAPI, ConvertAPI, FundingAPI, PublicAPI
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.stop_limit import StopLimit
from blankly.utils.exceptions import APIException, InvalidOrder


class OkexInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 180, 300, 1800, 3600, 7200, 14400])

        self._market: MarketAPI = self.calls['market']
        self._account: AccountAPI = self.calls['user']
        self._trade: TradeAPI = self.calls['trade']
        self._convert: ConvertAPI = self.calls['convert']
        self._funding: FundingAPI = self.calls['funding']
        self._public: PublicAPI = self.calls['public']

    def init_exchange(self):
        # This is purely an authentication check which can be disabled in settings
        fees = self._account.get_fee_rates('SPOT')
        try:
            if fees['message'] == "Invalid API Key":
                raise LookupError("Invalid API Key. Please check if the keys were input correctly into your "
                                  "keys.json.")
        except KeyError:
            pass

    def get_products(self): #get-ticker under market
        instrument_type = "SPOT"
        needed = self.needed['get_products']
        products = self._public.get_instruments(instrument_type)

        for i in range(len(products)):
            products[i]["base_asset"] = products[i].pop("baseCcy")
            products[i]["quote_asset"] = products[i].pop("quoteCcy")
            products[i]["base_min_size"] = products[i].pop("minSz")
            products[i]["base_max_size"] = 1000000000
            products[i]["base_increment"] = products[i].pop("tickSz")
            products[i] = utils.isolate_specific(needed, products[i])
        return products


    def get_account(self, symbol=None) -> utils.AttributeDict:
        pass
        # """
        #    Get all currencies in an account, or sort by symbol
        #    Args:
        #        symbol (Optional): Filter by particular symbol
        #        These arguments are mutually exclusive
        # """
        # symbol = super().get_account(symbol=symbol)
        # needed = self.needed['get_account']
        # """
        # {
        #     "code": "0",
        #     "data":
        #     [
        #         {
        #             "adjEq": "10679688.0460531643092577",
        #             "details": [
        #                 {
        #                     "availBal": "",
        #                     "availEq": "9930359.9998",
        #                     "cashBal": "9930359.9998",
        #                     "ccy": "USDT",
        #                     "crossLiab": "0",
        #                     "disEq": "9439737.0772999514",
        #                     "eq": "9930359.9998",
        #                     "eqUsd": "9933041.196999946",
        #                     "frozenBal": "0",
        #                     "interest": "0",
        #                     "isoEq": "0",
        #                     "isoLiab": "0",
        #                     "isoUpl":"0",
        #                     "liab": "0",
        #                     "maxLoan": "10000",
        #                     "mgnRatio": "",
        #                     "notionalLever": "",
        #                     "ordFrozen": "0",
        #                     "twap": "0",
        #                     "uTime": "1620722938250",
        #                     "upl": "0",
        #                     "uplLiab": "0",
        #                     "stgyEq":"0"
        #                 },
        #             ],
        #             "imr": "3372.2942371050594217",
        #             "isoEq": "0",
        #             "mgnRatio": "70375.35408747017",
        #             "mmr": "134.8917694842024",
        #             "notionalUsd": "33722.9423710505978888",
        #             "ordFroz": "0",
        #             "totalEq": "11172992.1657531589092577",
        #             "uTime": "1623392334718"
        #         }
        #     ],
        #     "msg": ""
        # }
        # """
        #
        # # if side == "buy":
        # #     available = self.local_account.get_account(quote)['available']
        # #     # Loose the funds when buying
        # #     self.local_account.update_available(quote, available - (size * price))
        # #
        # #     # Gain the funds on hold when buying
        # #     hold = self.local_account.get_account(quote)['hold']
        # #     self.local_account.update_hold(quote, hold + (size * price))
        # # elif side == "sell":
        # #     available = self.local_account.get_account(base)['available']
        # #     # Loose the size when selling
        # #     self.local_account.update_available(base, available - size)
        # #
        # #     # Gain size on hold when selling
        # #     hold = self.local_account.get_account(base)['hold']
        # #     self.local_account.update_hold(base, hold + size)
        #
        #
        # accounts = self._funding.get_balances()
        # parsed_dictionary = utils.AttributeDict({})
        # # We have to sort through it if the accounts are none
        # if symbol is not None:
        #     for i in accounts:
        #         if i["ccy"] == symbol:
        #             total_hold = 0
        #             order_info = self.calls.get_order_list()
        #             hold_value = order_info['data']['px']
        #             total_hold = total_hold + hold_value
        #             parsed_value = utils.isolate_specific(needed, i)
        #             dictionary = utils.AttributeDict({
        #                 'available': parsed_value['availBal'],
        #                 'hold': total_hold # check if being bought or sold and perform hold calculation accordingly
        #             })
        #             return dictionary
        #     raise ValueError("Symbol not found")
        # for i in range(len(accounts)):
        #     parsed_dictionary[accounts[i]['currency']] = utils.AttributeDict({
        #         'available': float(accounts[i]['available']),
        #         'hold': float(accounts[i]['holds'])
        #     })
        #
        # return parsed_dictionary

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

        response = self._trade.place_order(symbol, 'cash', side, 'market', size)
        if "sMsg" in response:
            raise InvalidOrder("Invalid Order: " + response["sMsg"])
        response["created_at"] = time.time()
        response["id"] = response.pop('ordId')
        response["status"] = response.pop('sCode')
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

        response = self._trade.place_order(symbol, 'cash', side, 'limit', size, px=price)
        if "sMsg" in response:
            raise InvalidOrder("Invalid Order: " + response["sMsg"])

        response_details = self._trade.get_orders(symbol, ordId=response['ordId'])

        response_details["created_at"] = response_details.pop('cTime')
        response_details["id"] = response_details.pop('ordId')
        response_details["status"] = response_details.pop('state')
        response_details = utils.isolate_specific(needed, response)
        return LimitOrder(order, response_details, self)

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        Returns:
            dict: Containing the order_id of cancelled order. Example::
            { "client_oid": "order123", }
        """
        return {"order_id": self._trade.cancel_order(symbol, ordId=order_id)}

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
            orders = list(self._trade.get_order_list(instType=symbol))

        if len(orders) == 0:
            return []
        if orders[0] == 'message':
            raise InvalidOrder("Invalid Order: " + str(orders))

        for i in range(len(orders)):
            orders[i]["created_at"] = orders[i].pop("cTime")
            needed = self.choose_order_specificity(orders[i]['ordType'])
            orders[i]["symbol"] = orders[i].pop('instId')
            orders[i]["id"] = orders[i].pop('ordId')
            orders[i]["status"] = orders[i].pop('state')
            if orders[i]["ordType"] == "limit":
                orders[i]["time_in_force"] = 'GTC'
            orders[i] = utils.isolate_specific(needed, orders[i])

        return orders

    def get_order(self, symbol, order_id) -> dict:
        response = self._trade.get_orders(symbol, ordId=order_id)

        if 'message' in response:
            raise APIException("Invalid: " + str(response['message']) + ", was the order canceled?")

        if response['ordType'] == 'market':
            needed = self.needed['market_order']
        elif response['ordType'] == 'limit':
            needed = self.needed['limit_order']
        else:
            needed = self.needed['market_order']

        response["symbol"] = response.pop('instId')
        response["id"] = response.pop('ordId')
        response["status"] = response.pop('state')
        response["time_in_force"] = None # gtc?
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
        fees = self._account.get_fee_rates("SPOT")
        fees['taker_fee_rate'] = fees['data'].pop('taker')
        fees['maker_fee_rate'] = fees['data'].pop('maker')
        return utils.isolate_specific(needed, fees)

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        resolution = blankly.time_builder.time_interval_to_seconds(resolution)

        epoch_start = int(utils.convert_epochs(epoch_start))
        epoch_stop = int(utils.convert_epochs(epoch_stop))

        accepted_grans = [60, 180, 300, 1800, 3600, 7200, 14400]

        if resolution not in accepted_grans:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = accepted_grans[min(range(len(accepted_grans)),
                                            key=lambda i: abs(accepted_grans[i] - resolution))]

        resolution = int(resolution)

        lookup_dict = {
            60: '1m',
            180: '3m',
            300: '5m',
            900: '15m',
            1800: '30m',
            3600: '1H',
            7200: '2H',
            14400: '4H',
        }

        gran_string = lookup_dict[resolution]

        need = int(epoch_stop + 300 * resolution)
        initial_need = need
        window_open = epoch_start
        history = []
        # Iterate while its more than max
        while epoch_start <= need:
            # Close is always 300 points ahead
            window_close = int(window_open + 300 * resolution)
            response = self._market.get_history_candlesticks(symbol, before=epoch_start, bar=gran_string, limit=300)
            if isinstance(response, dict):
                raise APIException(response['message'])
            history = history + response

            window_open = window_close
            epoch_start += (300 * resolution)
            time.sleep(.2)
            utils.update_progress((initial_need - need) / initial_need)

        # Fill the remainder
        # open_iso = utils.iso8601_from_epoch(window_open)
        # close_iso = utils.iso8601_from_epoch(epoch_stop)
        response = self._market.get_history_candlesticks(symbol, before=epoch_start, bar=gran_string, limit=300)
        if isinstance(response, dict):
            raise APIException(response['message'])
        history_block = history + response
        history_block.sort(key=lambda x: x[0])

        df = pd.DataFrame(history_block, columns=['time', 'low', 'high', 'open', 'close', 'volume', 'volume_currency'])
        # Have to cast this for some reason
        df = df.drop(columns=['volume_currency'])
        df[['time']] = df[['time']].astype(int)
        df[['low', 'high', 'open', 'close', 'volume']] = df[['low', 'high', 'open', 'close', 'volume']].astype(float)

        return df

    def get_order_filter(self, symbol: str) -> dict:
        instrument_type = "SPOT"
        response = self._public.get_instruments(instrument_type)
        products = None
        for i in response:
            if i["uly"] == symbol:
                products = i
                break

        base_min_size = float(products.pop('minSz'))
        # base_max_size = 100000000   #This value was hardcoded
        base_increment = float(products.pop('tickSz'))

        return {
            "symbol": products.pop('uly'),
            "base_asset": products.pop('baseCcy'),
            "quote_asset": products.pop('quoteCcy'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": 100000000,  # Maximum size to buy, this value was hardcoded
                "base_increment": base_increment,  # Specifies the minimum increment
                # for the base_asset.
                "price_increment": 0.1,

                "min_price": 0.1,
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,

                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": 100000000,  # Maximum size to buy, this value was hardcoded
                "base_increment": base_increment,  # Specifies the minimum increment

                "quote_increment": 0.1,  # Specifies the min order price as well
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
        response = self._market.get_index_ticker(instId=symbol)
        if 'message' in response:
            raise APIException("Error: " + response['message'])
        return float(response['idxPx'])
