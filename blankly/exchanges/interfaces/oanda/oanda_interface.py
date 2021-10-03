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

from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils import time_interval_to_seconds, utils as utils
import warnings
import pandas as pd
from datetime import datetime as dt
from typing import Union
import time
import dateparser as dp

from blankly.utils.exceptions import APIException

# todo: add the decorator for the error handling


class OandaInterface(ExchangeInterface):
    def __init__(self, authenticated_API: OandaAPI, preferences_path: str):
        super().__init__('oanda', authenticated_API, preferences_path, valid_resolutions=[5, 10, 15, 30, 60,
                                                                                          60 * 2, 60 * 4, 60 * 5,
                                                                                          60 * 10, 60 * 15, 60 * 30,
                                                                                          60 * 60, 60 * 60 * 24,
                                                                                          60 * 60 * 24 * 7,
                                                                                          60 * 60 * 24 * 30])
        assert isinstance(self.calls, OandaAPI)

    def init_exchange(self):
        assert isinstance(self.calls, OandaAPI)
        account_info = self.calls.get_account()
        assert account_info['account']['id'] is not None, "Oanda exchange account does not exist"

        self.__exchange_properties = {
            "maker_fee_rate": 0,
            "taker_fee_rate": 0
        }
        self.default_trunc = self._get_default_truncation()

    def get_products(self) -> dict:
        assert isinstance(self.calls, OandaAPI)
        needed = self.needed['get_products']
        instruments = self.calls.get_account_instruments()['instruments']

        for instrument in instruments:
            instrument['symbol'] = instrument.pop('name')
            currencies = instrument['symbol'].split('_')
            instrument['base_asset'] = currencies[0]
            instrument['quote_asset'] = currencies[1]
            instrument['base_min_size'] = float(instrument['minimumTradeSize'])
            instrument['base_max_size'] = float(instrument['maximumOrderUnits'])
            instrument['base_increment'] = 10 ** (-1 * int(instrument['tradeUnitsPrecision']))

        for i in range(len(instruments)):
            instruments[i] = utils.isolate_specific(needed, instruments[i])

        return instruments

    @property
    def cash(self) -> float:
        assert isinstance(self.calls, OandaAPI)
        account_dict = self.calls.get_account()['account']
        return float(account_dict['balance'])

    def get_account(self, symbol=None) -> utils.AttributeDict:
        assert isinstance(self.calls, OandaAPI)
        positions_dict = utils.AttributeDict({})
        positions = self.calls.get_all_positions()['positions']
        for position in positions:
            positions_dict[position['instrument']] = utils.AttributeDict({
                'available': float(position['long']['units']) - float(position['short']['units']),
                'hold': 0.0
            })

        positions_dict['USD'] = utils.AttributeDict({
            'available': self.cash,
            'hold': 0.0
        })

        # Now query all open orders and accordingly adjust
        open_orders = self.calls.get_all_open_orders()['orders']
        for position in open_orders:
            # todo: handle other types of orders
            if position['type'] == 'LIMIT':
                if float(position['units']) > 0:
                    positions_dict['USD']['available'] -= float(position['units']) * float(position['price'])
                    positions_dict['USD']['hold'] += float(position['units']) * float(position['price'])
                else:
                    instrument = position['instrument']
                    # sell orders just have a negative 'units'
                    positions_dict[instrument]['available'] -= (-1 * float(position['units']))
                    positions_dict[instrument]['hold'] += (-1 * float(position['units']))

        if symbol is not None:
            if symbol in positions_dict:
                return utils.AttributeDict({
                    'available': positions_dict[symbol]['available'],
                    'hold': positions_dict[symbol]['hold']
                })
            else:
                return utils.AttributeDict({
                    'available': 0.0,
                    'hold': 0.0
                })

        return positions_dict

    # funds is the base asset (EUR_CAD the base asset is CAD)
    def market_order(self, symbol: str, side: str, funds: float) -> MarketOrder:
        assert isinstance(self.calls, OandaAPI)

        qty_to_buy = funds / self.get_price(symbol)
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
            'funds': qty_to_buy,
            'side': side,
            'symbol': symbol,
            'type': 'market'
        }

        resp['symbol'] = resp['orderCreateTransaction']['instrument']
        resp['id'] = resp['orderCreateTransaction']['id']
        resp['created_at'] = resp['orderCreateTransaction']['time']
        resp['funds'] = qty_to_buy
        resp['status'] = "active"
        resp['type'] = 'market'
        resp['side'] = side

        resp = utils.isolate_specific(needed, resp)
        return MarketOrder(order, resp, self)

    def limit_order(self, symbol: str, side: str, price: float, quantity: int) -> LimitOrder:
        assert isinstance(self.calls, OandaAPI)
        if side == "buy":
            pass
        elif side == "sell":
            quantity *= -1
        else:
            raise ValueError("side needs to be either sell or buy")

        resp = self.calls.place_limit_order(symbol, quantity, price)
        needed = self.needed['limit_order']
        order = {
            'size': quantity,
            'side': side,
            'price': price,
            'symbol': symbol,
            'type': 'limit'
        }

        resp['symbol'] = resp['orderCreateTransaction']['instrument']
        resp['id'] = resp['orderCreateTransaction']['id']
        resp['created_at'] = resp['orderCreateTransaction']['time']
        resp['price'] = price
        resp['size'] = quantity
        resp['status'] = "active"
        resp['time_in_force'] = 'GTC'
        resp['type'] = 'limit'
        resp['side'] = side

        resp = utils.isolate_specific(needed, resp)
        return LimitOrder(order, resp, self)

    def cancel_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        resp = self.calls.cancel_order(order_id)
        return {'order_id': order_id}

    def get_open_orders(self, symbol=None):
        assert isinstance(self.calls, OandaAPI)
        if symbol is None:
            resp = self.calls.get_all_open_orders()
        else:
            resp = self.calls.get_orders(symbol)

        orders = resp['orders']

        for i in range(len(orders)):
            orders[i] = self.homogenize_order(orders[i])
        return orders

    def get_order(self, symbol, order_id) -> dict:
        # Either the Order’s OANDA-assigned OrderID or the Order’s client-provided ClientID prefixed by the “@” symbol
        assert isinstance(self.calls, OandaAPI)
        order = self.calls.get_order(order_id)
        if 'errorCode' in order:
            raise APIException(str(order))

        return self.homogenize_order(order['order'])

    def get_fees(self):
        assert isinstance(self.calls, OandaAPI)
        return {
            'maker_fee_rate': 0.0,
            'taker_fee_rate': 0.0
        }

    def get_product_history(self, symbol: str, epoch_start: float, epoch_stop: float, resolution: int):
        assert isinstance(self.calls, OandaAPI)

        resolution = utils.time_interval_to_seconds(resolution)

        supported_multiples = {5: "S5", 10: "S10", 15: "S15", 30: "S30", 60: "M1", 60 * 2: "M2",
                               60 * 4: "M4", 60 * 5: "M5", 60 * 10: "M10", 60 * 15: "M15", 60 * 30: "M30",
                               60 * 60: "H1", 60 * 60 * 24: "D", 60 * 60 * 24 * 7: "W", 60 * 60 * 24 * 30: "M"}

        multiples_keys = supported_multiples.keys()
        if resolution not in multiples_keys:
            utils.info_print("Granularity is not an accepted granularity...rounding to nearest valid value.")
            resolution = multiples_keys[min(range(len(multiples_keys)),
                                            key=lambda i: abs(multiples_keys[i] - resolution))]

        found_multiple, row_divisor = self.__evaluate_multiples(multiples_keys, resolution)

        candles = \
            self.calls.get_candles_by_startend(symbol, supported_multiples[found_multiple], epoch_start, epoch_stop)[
                'candles']

        result = []
        for candle in candles:
            ohlc = candle['mid']
            result.append([int(float(candle['time'])), ohlc['o'], ohlc['h'], ohlc['l'], ohlc['c'], candle['volume']])

        df = pd.DataFrame(result, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        dtypes = {"time": "int64", "open": "float32", "high": "float32", "low": "float32", "close": "float32",
                  "volume": "float32"}

        df = df.astype(dtypes)
        print(candles)

        return df

    def history(self,
                symbol: str,
                to: Union[str, int] = 200,
                resolution: Union[str, int] = '1d',
                start_date: Union[str, dt, float] = None,
                end_date: Union[str, dt, float] = None,
                return_as: str = 'df'):
        assert isinstance(self.calls, OandaAPI)

        if not to and not start_date:
            raise ValueError("history() call needs only 1 of {start_date, to} defined")
        if to and start_date:
            raise ValueError("history() call needs 1 of {start_date, to} defined")

        start_date = self._handle_input_time_conv(end_date)
        end_date = self._handle_input_time_conv(end_date)

        supported_multiples = {5: "S5", 10: "S10", 15: "S15", 30: "S30", 60: "M1", 60 * 2: "M2",
                               60 * 4: "M4", 60 * 5: "M5", 60 * 10: "M10", 60 * 15: "M15", 60 * 30: "M30",
                               60 * 60: "H1", 60 * 60 * 24: "D", 60 * 60 * 24 * 7: "W", 60 * 60 * 24 * 30: "M"}

        multiples_keys = supported_multiples.keys()
        # convert resolution into epoch seconds
        resolution_seconds = time_interval_to_seconds(resolution)

        found_multiple, row_divisor = self.__evaluate_multiples(multiples_keys, resolution_seconds)

        if to:
            aggregated_limit = to * row_divisor
            candles = self.calls.get_last_k_candles(symbol, supported_multiples[found_multiple], int(end_date), aggregated_limit)['candles']
        else:
            candles = self.calls.get_candles_by_startend(symbol, supported_multiples[found_multiple], int(start_date), int(end_date))['candles']

        result = []
        for candle in candles:
            ohlc = candle['mid']
            result.append([int(float(candle['time'])), ohlc['o'], ohlc['h'], ohlc['l'], ohlc['c'], candle['volume']])

        df = pd.DataFrame(result, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        dtypes = {"time": "int64", "open": "float32", "high": "float32", "low": "float32", "close": "float32",
                  "volume": "float32"}

        df = df.astype(dtypes)

        history = utils.get_ohlcv(df, row_divisor, from_zero=True)

        return super().cast_type(history, return_as=return_as)

    def get_order_filter(self, symbol: str):
        assert isinstance(self.calls, OandaAPI)
        resp = self.calls.get_account_instruments(symbol)['instruments'][0]
        resp['symbol'] = resp.pop('name')
        currencies = resp['symbol'].split('_')
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
        assert isinstance(self.calls, OandaAPI)
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
        if order['type'] == "MARKET":
            order['type'] = 'market'
            if float(order['units']) < 0:
                order['side'] = 'sell'
            else:
                order['side'] = 'buy'
            order['time_in_force'] = 'GTC'
            renames = [['instrument', 'symbol'],
                       ['createTime', 'created_at'],
                       ['state', 'status'],  # TODO: handle status
                       ['units', 'funds']]  # TODO: I think this is wrong
            order = utils.rename_to(renames, order)

        elif order['type'] == "LIMIT":
            order['type'] = 'limit'
            if float(order['units']) < 0:
                order['side'] = 'sell'
            else:
                order['side'] = 'buy'
            order['time_in_force'] = 'GTC'
            renames = [['instrument', 'symbol'],
                       ['createTime', 'created_at'],
                       ['state', 'status'],  # TODO: handle status
                       ['units', 'size']]
            order = utils.rename_to(renames, order)
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
