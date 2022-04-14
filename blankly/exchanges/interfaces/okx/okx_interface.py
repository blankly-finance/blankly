import time
import pandas as pd
import blankly.utils.time_builder
import blankly.utils.utils as utils
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.okx.okx_api import MarketAPI, AccountAPI, TradeAPI, ConvertAPI, FundingAPI, PublicAPI
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils.exceptions import APIException, InvalidOrder


class OkxInterface(ExchangeInterface):
    def __init__(self, exchange_name, authenticated_api):
        self._market: MarketAPI = authenticated_api['market']
        self._account: AccountAPI = authenticated_api['account']
        self._trade: TradeAPI = authenticated_api['trade']
        self._convert: ConvertAPI = authenticated_api['convert']
        self._funding: FundingAPI = authenticated_api['funding']
        self._public: PublicAPI = authenticated_api['public']
        super().__init__(exchange_name, authenticated_api, valid_resolutions=[60, 180, 300, 1800, 3600, 7200,
                                                                              14400, 21600, 43200, 86400, 604800,
                                                                              2629746, 7889238, 15778476, 31556952])

    def init_exchange(self):
        # This is purely an authentication check which can be disabled in settings
        # todo: change get_fee_rates
        fees = self._account.get_fee_rates(instType='SPOT', instId='BTC-USDT')
        try:
            if fees['msg'] == "Invalid API Key":
                raise LookupError("Invalid API Key. Please check if the keys were input correctly into your "
                                  "keys.json.")
        except KeyError:
            pass

    def get_products(self):
        instrument_type = "SPOT"
        needed = self.needed['get_products']
        products = self._public.get_instruments(instrument_type)

        for i in range(len(products['data'])):
            products['data'][i]["symbol"] = products['data'][i]["instId"]
            products['data'][i]["base_asset"] = products['data'][i]["baseCcy"]
            products['data'][i]["quote_asset"] = products['data'][i]["quoteCcy"]
            products['data'][i]["base_min_size"] = products['data'][i]["minSz"]
            products['data'][i]["base_max_size"] = 1000000000
            products['data'][i]["base_increment"] = products['data'][i]["tickSz"]
            products['data'][i] = utils.isolate_specific(needed, products['data'][i])
        return products['data']


    def get_account(self, symbol=None) -> utils.AttributeDict:
        """
           Get all currencies in an account, or sort by symbol
           Args:
               symbol (Optional): Filter by particular symbol
               These arguments are mutually exclusive
        """

        symbol = super().get_account(symbol=symbol)
        needed = self.needed['get_account']
        accounts = self._account.get_account()

        parsed_dictionary = utils.AttributeDict({})
        #We have to sort through it if the accounts are none
        if symbol is not None:
            accounts_specific = self._account.get_account(symbol)
            if accounts_specific['code'] == 51000 or accounts_specific['code'] == 51001:
                raise ValueError("Symbol not found")
            for i in accounts_specific['data']:
                parsed_value = utils.isolate_specific(needed, i)
                dictionary = utils.AttributeDict({
                    'available': float(parsed_value['exchange_specific']['details'][0]['availBal']), # accounts_specific['data'][0]['details'][0]['availBal'],
                    'hold': float(parsed_value['exchange_specific']['details'][0]['frozenBal'])
                })
                return dictionary
        for i in range(len(accounts['data'][0]['details'])):
            parsed_dictionary[accounts['data'][0]['details'][i]['ccy']] = utils.AttributeDict({
                'available': float(accounts['data'][0]['details'][i]['availBal']),
                'hold': float(accounts['data'][0]['details'][i]['frozenBal'])
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

        response = self._trade.place_order(symbol, 'cash', side, 'market', size)
        if len(response['data'][0]['sMsg']) != 0:
            raise InvalidOrder("Invalid Order: " + response['data'][0]["sMsg"])
        response["created_at"] = time.time()
        response["id"] = response['data'][0]['ordId']
        response["status"] = response['data'][0]['sCode']
        response["symbol"] = symbol
        response["size"] = size
        response["side"] = side
        response["type"] = 'market'
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
        if len(response['data'][0]['sMsg']) != 0:
            raise InvalidOrder("Invalid Order: " + response['data'][0]["sMsg"])

        response_details = self._trade.get_orders(symbol, ordId=response['data'][0]['ordId'])

        response_details["created_at"] = response_details['data'][0]['cTime']
        response_details["id"] = response_details['data'][0]['ordId']
        response_details["status"] = response_details['data'][0]['state']
        response_details["symbol"] = response_details['data'][0]['instId']
        response_details["size"] = response_details['data'][0]['sz']
        response_details["side"] = response_details['data'][0]['side']
        response_details["price"] = response_details['data'][0]['px']
        response_details["type"] = response_details['data'][0]['ordType']
        response_details["time_in_force"] = 'GTC'

        response_details = utils.isolate_specific(needed, response_details)
        return LimitOrder(order, response_details, self)

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        Returns:
            dict: Containing the order_id of cancelled order. Example::
            { "client_oid": "order123", }
        """
        response = self._trade.cancel_order(symbol, ordId=order_id)
        return {"order_id": response['data'][0]['ordId']}

    def get_open_orders(self,
                        symbol: str = None) -> list:
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
            orders = self._trade.get_order_list()
        else:
            orders = self._trade.get_order_list(instId=symbol)

        if len(orders['data']) == 0:
            return []
        if orders['code'].startswith('5'):
            raise InvalidOrder("Invalid Order: " + str(orders))

        for i in range(len(orders['data'])):
            orders['data'][i]["created_at"] = orders['data'][i]["cTime"]
            needed = self.choose_order_specificity(orders['data'][i]['ordType'])
            orders['data'][i]["symbol"] = orders['data'][i]['instId']
            orders['data'][i]["id"] = orders['data'][i]['ordId']
            orders['data'][i]["status"] = orders['data'][i]['state']
            orders['data'][i]["size"] = orders['data'][i]['sz']
            orders['data'][i]["price"] = orders['data'][i]['px']
            orders['data'][i]["type"] = orders['data'][i]["ordType"]
            if orders['data'][i]["ordType"] == "limit":
                orders['data'][i]["time_in_force"] = 'GTC'
            orders['data'][i] = utils.isolate_specific(needed, orders['data'][i])

        return orders['data']

    def get_order(self, symbol, order_id) -> dict:
        response = self._trade.get_orders(symbol, ordId=order_id)

        if 'message' in response:
            raise APIException("Invalid: " + str(response['msg']) + ", was the order canceled?")

        if response['data'][0]['ordType'] == 'market':
            needed = self.needed['market_order']
        elif response['data'][0]['ordType'] == 'limit':
            needed = self.needed['limit_order']
            response['price'] = response['data'][0]['px']
        else:
            needed = self.needed['market_order']

        response["symbol"] = response['data'][0]['instId']
        response["created_at"] = response['data'][0]['cTime']
        response["size"] = response['data'][0]['sz']
        response["side"] = response['data'][0]['side']
        response["type"] = response['data'][0]['ordType']
        response["id"] = response['data'][0]['ordId']
        response["status"] = response['data'][0]['state']
        response["time_in_force"] = 'GTC'
        return utils.isolate_specific(needed, response)

    def get_fees(self, symbol) -> dict:
        needed = self.needed['get_fees']
        """
        {
            "category": "1",
            "maker": "0.0002",
            "taker": "0.0005",
            "timestamp": "2019-12-11T11:02:31.360Z"
        }
        """
        if symbol is None:
            raise ValueError("There was no symbol inputted, please try again.")
        else:
            fees = self._account.get_fee_rates(instType="SPOT", instId=symbol)
        fees['taker_fee_rate'] = fees['data'][0]['taker']
        fees['maker_fee_rate'] = fees['data'][0]['maker']
        return utils.isolate_specific(needed, fees)

    def overridden_history(self, symbol, epoch_start, epoch_stop, resolution, **kwargs) -> pd.DataFrame:
        """
        Okx is strange
        """
        to = kwargs['to']

        if isinstance(to, str):
            epoch_start = epoch_start - resolution
        elif isinstance(to, int):
            epoch_start = epoch_start - resolution

        return self.get_product_history(symbol, epoch_start, epoch_stop, resolution)

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        if epoch_stop > time.time():
            epoch_stop = int(time.time())

        resolution = blankly.time_builder.time_interval_to_seconds(resolution)

        init_epoch_start = int(epoch_start * 1000)
        init_epoch_stop = int(epoch_stop * 1000)

        accepted_grans = [60, 180, 300, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 604800, 2629746, 7889238, 15778476, 31556952]

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
            21600: '6H',
            43200: '12H',
            86400: '1D',
            604800: '1W',
            2629746: '1M',
            7889238: '3M',
            15778476: '6M',
            31556952: '1Y'
        }

        gran_string = lookup_dict[resolution]

        history = []
        while init_epoch_start < init_epoch_stop + resolution * 100 * 1100:
            response = self._market.get_history_candlesticks(symbol, after=init_epoch_start, bar=gran_string, limit=100)

            if len(response['data']) != 0:
                history = history + response['data']
            init_epoch_start = init_epoch_start + (100 * 1000 * resolution)

        history.sort(key=lambda x: x[0])
        new_history = list(set(tuple(sub) for sub in history))
        new_history.sort(key=lambda x: x[0])
        df = pd.DataFrame(new_history, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'volume_currency'])
        df = df.drop(columns=['volume_currency'])
        df[['time']] = df[['time']].astype('int64').div(1000).astype(int)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        # df.plot(x='time', y='close', kind='scatter')
        df = df[df['time'] >= epoch_start]
        df = df[df['time'] <= epoch_stop]
        # plt.show()

        return df

    def get_order_filter(self, symbol: str) -> dict:
        instrument_type = "SPOT"
        response = self._public.get_instruments(instrument_type)
        products = None
        for i in response["data"]:
            if i["instId"] == symbol:
                products = i
                break

        base_min_size = float(products.pop('minSz'))
        base_increment = float(products.pop('tickSz'))

        return {
            "symbol": products.pop('uly'),
            "base_asset": products.pop('baseCcy'),
            "quote_asset": products.pop('quoteCcy'),
            "max_orders": 1000000000000,
            "limit_order": {
                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": 100000000,  # Maximum size to buy, this value was hardcoded
                "base_increment": base_increment,  # Specifies the minimum increment for the base_asset.
                "price_increment": 0.1,

                "min_price": 0.1,
                "max_price": 9999999999,
            },
            'market_order': {
                "fractionable": True,

                "base_min_size": base_min_size,  # Minimum size to buy
                "base_max_size": 100000000,  # Maximum size to buy, this value was hardcoded
                "base_increment": base_increment,  # Specifies the minimum increment

                "quote_increment": 0.1,  # Specifies the min order price as well as the price increment.
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
        if len(response['msg']) != 0:
            raise APIException("Error: " + response['msg'])
        return float(response['data'][0]['idxPx'])


