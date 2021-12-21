"""
    Interface for communicating with Oanda
    Copyright (C) 2021  Arun Annamalai

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
import dateparser as dp
from datetime import datetime as dt
from typing import Union

import pandas as pd

from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils import utils as utils
from blankly.utils.exceptions import APIException


class OandaInterface(ExchangeInterface):
    def __init__(self, authenticated_api: OandaAPI, preferences_path: str):
        self.default_trunc = None
        super().__init__('oanda', authenticated_api, preferences_path, valid_resolutions=[5, 10, 15, 30, 60,
                                                                                          60 * 2, 60 * 4, 60 * 5,
                                                                                          60 * 10, 60 * 15, 60 * 30,
                                                                                          60 * 60, 60 * 60 * 24,
                                                                                          60 * 60 * 24 * 7,
                                                                                          60 * 60 * 24 * 30])
        self.supported_multiples = {5: "S5", 10: "S10", 15: "S15", 30: "S30", 60: "M1", 60 * 2: "M2",
                                    60 * 4: "M4", 60 * 5: "M5", 60 * 10: "M10", 60 * 15: "M15", 60 * 30: "M30",
                                    60 * 60: "H1", 60 * 60 * 24: "D", 60 * 60 * 24 * 7: "W", 60 * 60 * 24 * 30: "M"}

        self.multiples_keys = list(self.supported_multiples.keys())

        self.unique_assets = None

        self.max_candles = 5000

        self.calls: OandaAPI

    def init_exchange(self):
        account_info = self.calls.get_account()
        if 'errorMessage' in account_info:
            raise LookupError(f"{account_info['errorMessage']}. \nTry toggling the \'use_sandbox\' setting "
                              "in your settings.json or check if the keys were input correctly into your "
                              "keys.json.")
        assert account_info['account']['id'] is not None, "Oanda exchange account does not exist"

        self.default_trunc = self._get_default_truncation()

        filtered_assets = []
        products = self.get_products()
        for i in products:
            base = utils.get_base_asset(i['symbol'])
            quote = utils.get_quote_asset(i['symbol'])
            if base not in filtered_assets:
                filtered_assets.append(base)
            if quote not in filtered_assets:
                filtered_assets.append(quote)

        self.unique_assets = filtered_assets

    def get_products(self) -> list:
        """
        Insturments response:
            {
                'name': 'GBP_NZD',
                'type': 'CURRENCY',
                'displayName': 'GBP/NZD',
                'pipLocation': -4,
                'displayPrecision': 5,
                'tradeUnitsPrecision': 0,
                'minimumTradeSize': '1',
                'maximumTrailingStopDistance': '1.00000',
                'minimumTrailingStopDistance': '0.00050',
                'maximumPositionSize': '0',
                'maximumOrderUnits': '100000000',
                'marginRate': '0.03',
                'guaranteedStopLossOrderMode': 'DISABLED',
                'tags': [{
                    'type': 'ASSET_CLASS',
                    'name': 'CURRENCY'
                }],
                'financing': {
                    'longRate': '-0.0153',
                    'shortRate': '-0.0093',
                    'financingDaysOfWeek': [{
                        'dayOfWeek': 'MONDAY',
                        'daysCharged': 1
                    }, {
                        'dayOfWeek': 'TUESDAY',
                        'daysCharged': 1
                    }, {
                        'dayOfWeek': 'WEDNESDAY',
                        'daysCharged': 1
                    }, {
                        'dayOfWeek': 'THURSDAY',
                        'daysCharged': 1
                    }, {
                        'dayOfWeek': 'FRIDAY',
                        'daysCharged': 1
                    }, {
                        'dayOfWeek': 'SATURDAY',
                        'daysCharged': 0
                    }, {
                        'dayOfWeek': 'SUNDAY',
                        'daysCharged': 0
                    }]
            }
        }
        """
        needed = self.needed['get_products']
        instruments = self.calls.get_account_instruments()['instruments']

        for instrument in instruments:
            instrument['symbol'] = self.__convert_symbol_to_blankly(instrument.pop('name'))
            instrument['base_asset'] = utils.get_base_asset(instrument['symbol'])
            instrument['quote_asset'] = utils.get_quote_asset(instrument['symbol'])
            instrument['base_min_size'] = float(instrument['minimumTradeSize'])
            instrument['base_max_size'] = float(instrument['maximumOrderUnits'])
            instrument['base_increment'] = 10 ** (-1 * int(instrument['tradeUnitsPrecision']))

        for i in range(len(instruments)):
            instruments[i] = utils.isolate_specific(needed, instruments[i])

        return instruments

    def get_account(self, symbol=None) -> utils.AttributeDict:
        if symbol is not None:
            symbol = self.__convert_blankly_to_oanda(symbol)
        positions_dict = utils.AttributeDict({})
        positions = self.calls.get_all_positions()['positions']
        for position in positions:
            # Split both the base and the quote
            # This the base split [0]
            positions_dict[position['instrument'].split('_')[0]] = utils.AttributeDict({
                'available': float(position['long']['units']) - float(position['short']['units']),
                'hold': 0.0
            })
            # This is the quote split [1]
            positions_dict[position['instrument'].split('_')[1]] = utils.AttributeDict({
                'available': float(position['long']['units']) - float(position['short']['units']),
                'hold': 0.0
            })

        def cash():
            account_dict = self.calls.get_account()['account']
            return float(account_dict['balance'])

        positions_dict['USD'] = utils.AttributeDict({
            'available': cash(),
            'hold': 0.0
        })

        # Now query all open orders and accordingly adjust
        open_orders = self.calls.get_all_open_orders()['orders']
        for position in open_orders:
            # todo: handle other types of orders
            if position['type'] == 'LIMIT':
                instrument_sides = position['instrument'].split('_')
                if float(position['units']) > 0:
                    quote_currency = instrument_sides[1]
                    positions_dict[quote_currency]['available'] -= float(position['units']) * float(position['price'])
                    positions_dict[quote_currency]['hold'] += float(position['units']) * float(position['price'])
                else:
                    base_currency = instrument_sides[0]
                    # sell orders just have a negative 'units'
                    positions_dict[base_currency]['available'] -= (-1 * float(position['units']))
                    positions_dict[base_currency]['hold'] += (-1 * float(position['units']))

        # Note that now __unique assets could be uninitialized:
        if self.unique_assets is None:
            self.init_exchange()

        for i in self.unique_assets:
            if i not in positions_dict:
                positions_dict[i] = utils.AttributeDict({
                    'available': 0.0,
                    'hold': 0.0
                })

        if symbol is not None:
            if symbol in positions_dict:
                return utils.AttributeDict({
                    'available': positions_dict[symbol]['available'],
                    'hold': positions_dict[symbol]['hold']
                })
            else:
                raise KeyError('Symbol not found.')

        return positions_dict

    # funds is the base asset (EUR_CAD the base asset is CAD)
    @utils.order_protection
    def market_order(self, symbol: str, side: str, size: float) -> MarketOrder:
        symbol = self.__convert_blankly_to_oanda(symbol)

        # Make sure that default trunc has been established - init may have been skipped
        if self.default_trunc is None:
            self.init_exchange()

        qty_to_buy = size
        qty_to_buy = utils.trunc(qty_to_buy, self.default_trunc)

        # we need to round qty_to_buy

        if side == "buy":
            pass
        elif side == "sell":
            qty_to_buy *= -1
        else:
            raise ValueError("side needs to be either sell or buy")

        resp = self.calls.place_market_order(symbol, qty_to_buy)

        needed = self.needed['market_order']
        order = {
            'size': qty_to_buy,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }
        if 'orderRejectTransaction' in resp:
            raise APIException(resp['errorMessage'])
        resp['symbol'] = self.__convert_symbol_to_blankly(resp['orderCreateTransaction']['instrument'])
        resp['id'] = resp['orderCreateTransaction']['id']
        resp['created_at'] = resp['orderCreateTransaction']['time']
        resp['size'] = abs(qty_to_buy)
        resp['status'] = "active"
        resp['type'] = 'market'
        resp['side'] = side

        resp = utils.isolate_specific(needed, resp)
        return MarketOrder(order, resp, self)

    @utils.order_protection
    def limit_order(self, symbol: str, side: str, price: float, size: float) -> LimitOrder:
        symbol = self.__convert_blankly_to_oanda(symbol)
        if side == "buy":
            pass
        elif side == "sell":
            size *= -1
        else:
            raise ValueError("side needs to be either sell or buy")

        resp = self.calls.place_limit_order(symbol, size, price)
        needed = self.needed['limit_order']
        order = {
            'size': size,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }

        resp['symbol'] = self.__convert_symbol_to_blankly(resp['orderCreateTransaction']['instrument'])
        resp['id'] = resp['orderCreateTransaction']['id']
        resp['created_at'] = resp['orderCreateTransaction']['time']
        resp['price'] = price
        resp['size'] = abs(size)
        resp['status'] = "active"
        resp['time_in_force'] = 'GTC'
        resp['type'] = 'limit'
        resp['side'] = side

        resp = utils.isolate_specific(needed, resp)
        return LimitOrder(order, resp, self)

    def cancel_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        self.calls.cancel_order(order_id)
        return {'order_id': order_id}

    def get_open_orders(self, symbol=None):
        if symbol is None:
            resp = self.calls.get_all_open_orders()
        else:
            symbol = self.__convert_blankly_to_oanda(symbol)
            resp = self.calls.get_orders(symbol)

        orders = resp['orders']

        for i in range(len(orders)):
            orders[i] = self.homogenize_order(orders[i])
        return orders

    def get_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        order = self.calls.get_order(order_id)
        return self.homogenize_order(order['order'])

    def get_fees(self):
        return {
            'maker_fee_rate': 0.0,
            'taker_fee_rate': 0.0
        }

    def overridden_history(self, symbol, epoch_start, epoch_stop, resolution, **kwargs) -> pd.DataFrame:
        resolution = self.multiples_keys[min(range(len(self.multiples_keys)),
                                             key=lambda i: abs(self.multiples_keys[i] - resolution))]
        symbol = self.__convert_blankly_to_oanda(symbol)
        if kwargs['to'] is not None:
            to = kwargs['to']

            frames = []

            while to > 0:
                # Grab candles 5k at a time
                frames.append(self.calls.get_last_k_candles(symbol, granularity=self.supported_multiples[resolution],
                                                            to_unix=epoch_stop, count=self.max_candles))

                # Step back
                epoch_stop = epoch_stop - (resolution * self.max_candles)
                to = to - self.max_candles

            # Then just trim to the number of points that are required
            return self.format_oanda_df(frames, sort=True).iloc[-kwargs['to']:].reset_index(drop=True)

        else:
            return self.get_product_history(symbol, epoch_start, epoch_stop, resolution)

    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution: int):
        symbol = self.__convert_blankly_to_oanda(symbol)

        resolution = int(utils.time_interval_to_seconds(resolution))

        if resolution not in self.multiples_keys:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = self.multiples_keys[min(range(len(self.multiples_keys)),
                                                 key=lambda i: abs(self.multiples_keys[i] - resolution))]

        # Grab an entire window
        candles = []
        window_start = epoch_stop - (resolution * self.max_candles)
        window_end = epoch_stop
        ran_once = False
        while window_start > epoch_start or not ran_once:
            candles.append(self.calls.get_candles_by_startend(symbol,
                                                              self.supported_multiples[resolution],
                                                              window_start,
                                                              window_end))

            window_start = window_start - (resolution * self.max_candles)
            window_end = window_end - (resolution * self.max_candles)

            ran_once = True

        df = self.format_oanda_df(candles, sort=True)
        return df[df['time'] >= epoch_start].reset_index(drop=True)

    def get_order_filter(self, symbol: str):
        symbol = self.__convert_blankly_to_oanda(symbol)
        resp = self.calls.get_account_instruments(symbol)['instruments'][0]
        currencies = resp['name'].split('_')
        resp['symbol'] = self.__convert_symbol_to_blankly(resp.pop('name'))
        resp['base_asset'] = currencies[0]
        resp['quote_asset'] = currencies[1]
        resp['limit_order'] = {
            "base_min_size": float(resp['minimumTradeSize']),
            "base_max_size": float(resp['maximumOrderUnits']),
            "base_increment": 10 ** (-1 * int(resp['tradeUnitsPrecision'])),
            "price_increment": 0.01,
            "min_price": 0.00001,
            "max_price": 9999999999
        }
        price = self.get_price(symbol)
        resp['market_order'] = {
            "fractionable": True,

            "base_min_size": float(resp['minimumTradeSize']),  # Minimum size to buy
            "base_max_size": float(resp['maximumOrderUnits']),  # Maximum size to buy
            "base_increment": 10 ** (-1 * int(resp['tradeUnitsPrecision'])),  # Specifies the minimum increment

            "quote_increment": 0.01,
            "buy": {
                "min_funds": float(resp['minimumTradeSize']) * price,
                "max_funds": float(resp['maximumOrderUnits']) * price
            },
            "sell": {
                "min_funds": float(resp['minimumTradeSize']) * price,
                "max_funds": float(resp['maximumOrderUnits']) * price
            }
        }
        resp['max_orders'] = 10000
        needed = self.needed["get_order_filter"]
        resp = utils.isolate_specific(needed, resp)
        return resp

    def get_price(self, symbol: str) -> float:
        symbol = self.__convert_blankly_to_oanda(symbol)
        resp = self.calls.get_order_book(symbol)
        if 'errorMessage' in resp:
            # could be that this is instrument without order book so try using latest candle
            resp2 = self.calls.get_last_k_candles(symbol, 'S5', time.time(), 1)
            if 'errorMessage' in resp2:
                raise APIException(f'{symbol} did not have orderbook, so tried to use latest candle to '
                                   f'price. Here is the orderbook error ' + str(resp) + 'here is the candle error ' +
                                   str(resp2))
            return float(resp2['candles'][0]['mid']['c'])
        return float(resp['orderBook']['price'])

    def homogenize_order(self, order):
        def add_details(order_: dict):
            if float(order_['units']) < 0:
                order_['side'] = 'sell'
            else:
                order_['side'] = 'buy'
            order_['time_in_force'] = 'GTC'
            renames_ = [['instrument', 'symbol'],
                        ['createTime', 'created_at'],
                        ['state', 'status'],  # TODO: handle status
                        ['units', 'size']]
            return utils.rename_to(renames_, order_)
        if order['type'] == "MARKET":
            order['type'] = 'market'
            order = add_details(order)

        elif order['type'] == "LIMIT":
            order['type'] = 'limit'
            order = add_details(order)
        else:
            # TODO: handle other order types
            pass

        needed = self.choose_order_specificity(order['type'])
        order = utils.isolate_specific(needed, order)
        return order

    @staticmethod
    def __evaluate_multiples(valid_resolutions, resolution_seconds):
        found_multiple = -1
        for multiple in reversed(valid_resolutions):
            if resolution_seconds % multiple == 0:
                found_multiple = multiple
                break

        row_divisor = resolution_seconds / found_multiple
        row_divisor = int(row_divisor)

        if row_divisor > 100:
            raise Warning("The resolution you requested is an extremely high of the base resolutions supported and may "
                          "slow down the performance of your model: {} * {}".format(found_multiple, row_divisor))

        return found_multiple, row_divisor

    @staticmethod
    def _handle_input_time_conv(date: Union[str, dt, float] = None) -> float:
        if not date:
            return time.time()

        if isinstance(date, float):
            pass
        elif isinstance(date, str):
            date = dp.parse(date).timestamp()
        elif isinstance(date, dt):
            date = date.timestamp()
        else:
            raise ValueError("start and end time must be one of [str, float, datetime]")

        return date

    def _get_default_truncation(self) -> int:
        instruments = self.calls.get_account_instruments()['instruments']
        lowest_precision = int(instruments[0]['tradeUnitsPrecision'])
        for instrument in instruments:
            lowest_precision = min(lowest_precision, int(instrument['tradeUnitsPrecision']))
        return lowest_precision

    @staticmethod
    def __convert_symbol_to_blankly(symbol: str) -> str:
        return symbol.replace('_', '-')

    @staticmethod
    def __convert_blankly_to_oanda(symbol: str) -> str:
        return symbol.replace('-', '_')

    @staticmethod
    def format_oanda_df(candles: list, sort: bool = False):
        """
        Given an OANDA history type response, format it into a readable dataframe:
        Example index from a list response:

        (this is a 1 element list with a single query)
        [{'instrument': 'EUR_USD', 'granularity': 'H1', 'candles':
            [{'complete': True, 'volume': 1202, 'time': '1637114400.000000000', 'mid': {'o': '1.13232', 'h': '1.13242',
                'l': '1.13189', 'c': '1.13218'}},
            {'complete': True, 'volume': 4907, 'time': '1637118000.000000000', 'mid': {'o': '1.13216', 'h': '1.13220',
                'l': '1.12637', 'c': '1.12890'}},
            {'complete': True, 'volume': 2478, 'time': '1637121600.000000000', 'mid': {'o': '1.12891', 'h': '1.13015',
                'l': '1.12890', 'c': '1.12982'}}]
        }]

        This gets kind of weird because OANDA gives a list of responses:
        [resp1, resp2] where each response *might* have a candles key and inside a candles key
        is the actual data we need
        """
        result = []
        for single_response in candles:
            try:
                internal_candles = single_response['candles']
            except KeyError:
                # There must not be a candles key to even get to the mid.
                # This will generate an empty df
                internal_candles = []

            for single_candle in internal_candles:
                ohlc = single_candle['mid']
                result.append([int(float(single_candle['time'])),
                               ohlc['o'],
                               ohlc['h'],
                               ohlc['l'],
                               ohlc['c'],
                               single_candle['volume']])

        df = pd.DataFrame(result, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        dtypes = {"time": int, "open": float, "high": float, "low": float, "close": float,
                  "volume": float}
        if sort:
            return df.sort_values(by=['time'], ignore_index=True).astype(dtypes)
        else:
            return df.astype(dtypes)
