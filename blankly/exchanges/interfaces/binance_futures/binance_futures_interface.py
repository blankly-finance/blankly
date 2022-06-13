"""
    Binance Futures ExchangeInterface object.
    Copyright (C) 2022 Matias Kotlik

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
from operator import itemgetter
from typing import Optional

import binance.exceptions

from blankly.exchanges.interfaces.binance.binance_interface import BinanceInterface

try:
    from functools import cached_property
except ImportError:  # emerson is "too cool" for py3.8
    from functools import lru_cache


    def cached_property(func):
        return property(lru_cache(maxsize=None)(func))

from datetime import datetime as dt
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

import blankly
from blankly.utils import utils, time_builder
from blankly.enums import MarginType, PositionMode, Side, TimeInForce, HedgeMode, OrderType, ContractType, OrderStatus
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder

BINANCE_FUTURES_FEES = [
    (0.00020, 0.00040),
    (0.00016, 0.00040),
    (0.00014, 0.00035),
    (0.00012, 0.00032),
    (0.00010, 0.00030),
    (0.00008, 0.00027),
    (0.00006, 0.00025),
    (0.00004, 0.00022),
    (0.00002, 0.00020),
    (0.00000, 0.00017),
]


class BinanceFuturesInterface(FuturesExchangeInterface):
    calls: Client

    @staticmethod
    def to_exchange_symbol(symbol: str):
        return symbol.replace('-', '')

    # TODO binance SPOT should prob be refactored to do this at some point
    def to_blankly_symbol(self, symbol: str):
        return self.symbol_map[symbol]

    @cached_property
    def symbol_map(self):
        symbols = self.calls.futures_exchange_info()['symbols']
        return {
            symbol['symbol']: symbol['baseAsset'] + '-' + symbol['quoteAsset']
            for symbol in symbols
        }

    def __init__(self, exchange_name, authenticated_api):
        super().__init__(exchange_name, authenticated_api)

    def init_exchange(self):
        try:
            self.calls.futures_account()
        except BinanceAPIException as e:
            raise Exception(
                f"{e.error_message}. Are you trying to use your normal exchange keys while in sandbox mode? \nTry "
                "toggling the 'use_sandbox' setting in your settings.json or check if the keys were input "
                "correctly into your keys.json.")
        try:
            # force oneway mode
            self.calls.futures_change_position_mode(dualSidePosition=False)
        except binance.exceptions.BinanceAPIException as e:
            if e.code != -4059:  # re raise anything other than "already set"
                raise e

    def set_hedge_mode(self, hedge_mode: HedgeMode):
        is_hedge = True if hedge_mode == HedgeMode.HEDGE else False

        if self.calls.futures_get_position_mode(
        )['dualSidePosition'] != is_hedge:
            self.calls.futures_change_position_mode(dualSidePosition=is_hedge)

    def get_hedge_mode(self):
        is_hedge = self.calls.futures_get_position_mode()['dualSidePosition']
        return HedgeMode.HEDGE if is_hedge else HedgeMode.ONEWAY

    def get_leverage(self, symbol: str = None) -> float:
        if not symbol:
            raise Exception(
                'Binance Futures does not support account wide leverage. Use interface.get_leverage(leverage, '
                'symbol) to get leverage for a symbol. ')
        symbol = self.to_exchange_symbol(symbol)
        return float(
            self.calls.futures_position_information(
                symbol=symbol)[0]['leverage'])

    @utils.order_protection
    def set_leverage(self, leverage: float, symbol: str = None):
        if not symbol:
            raise Exception(
                'Binance Futures does not support account wide leverage. Use interface.set_leverage(leverage, '
                'symbol) to set leverage for each symbol you wish to trade. ')
        symbol = self.to_exchange_symbol(symbol)
        return self.calls.futures_change_leverage(
            symbol=symbol, leverage=leverage)['maxNotionalValue']

    @utils.order_protection
    def set_margin_type(self, symbol: str, type: MarginType):
        """
        Set margin type for a symbol.
        """
        symbol = self.to_exchange_symbol(symbol)
        try:
            self.calls.futures_change_margin_type(symbol=symbol,
                                                  marginType=type.upper())
        except BinanceAPIException as e:
            if e.code != -4046:  # -4046 NO_NEED_TO_CHANGE_MARGIN_TYPE (margin type is already set)
                raise e

    def get_margin_type(self, symbol: str):
        # binance doesn't have an API for this
        # an attempt to create a workaround is preserved below
        # proceed at your own risk
        raise NotImplementedError
        # symbol = self.to_exchange_symbol(symbol)
        #
        # # first check for open position
        # position = self.get_positions(symbol)
        # if position:
        #     return position.margin_type
        #
        # # to get the current margin type, try setting CROSSED and see if an exception is raised.
        # try:
        #     self.calls.futures_change_margin_type(
        #         symbol=symbol, marginType=MarginType.CROSSED.upper())
        # except BinanceAPIException as e:
        #     if e.code != -4046:  # -4046 NO_NEED_TO_CHANGE_MARGIN_TYPE (margin type is already set)
        #         return MarginType.CROSSED
        #
        # # if it actually changed, change it back to ISOLATED
        # self.calls.futures_change_margin_type(
        #     symbol=symbol, marginType=MarginType.ISOLATED.upper())
        # return MarginType.ISOLATED

    def get_products(self, filter: str = None) -> dict:
        # https://binance-docs.github.io/apidocs/futures/en/#exchange-information
        res = self.calls.futures_exchange_info()["symbols"]
        products = {}
        for prod in res:
            if '_' in prod['symbol']:
                continue  # don't support expiring contracts
            symbol = prod['baseAsset'] + '-' + prod['quoteAsset']
            products[symbol] = {
                'symbol': symbol,
                'base_asset': prod['baseAsset'],
                'quote_asset': prod['quoteAsset'],
                'contract_type': ContractType.PERPETUAL,
                'price_precision': int(prod['pricePrecision']),
                'size_precision': int(prod['quantityPrecision']),
                'exchange_specific': prod
            }

        if filter:
            return products[filter]
        return products

    def get_account(self, filter=None) -> dict:
        res = self.calls.futures_account()

        accounts = {}
        for asset in res['assets']:
            symbol = asset['asset']
            accounts[symbol] = {
                'available': float(asset['availableBalance']),
                'hold': 0.0,  # TODO
                'exchange_specific': asset,
            }

        if filter:
            return accounts[filter]
        return accounts

    def get_position(self, filter: str = None) -> Optional[dict]:
        account = self.calls.futures_account()

        positions = {}

        # write in data from binance
        for position in account['positions']:
            symbol = position['symbol']
            size = float(position['positionAmt'])
            if size == 0:
                continue  # don't show empty positions
            symbol = self.to_blankly_symbol(symbol)
            base, quote = symbol.split('-')
            margin = MarginType.ISOLATED \
                if position['isolated'] else MarginType.CROSSED
            positions[symbol] = {
                'symbol': symbol,
                'base_asset': base,
                'quote_asset': quote,
                'size': size,
                'leverage': float(position['leverage']),
                'margin_type': MarginType.ISOLATED if position.get('isolated', False) else MarginType.CROSSED,
                'position': PositionMode(position['positionSide'].lower()),
                'contract_type': ContractType.PERPETUAL,
                'exchange_specific': position
            }

        if filter:
            return positions.get(filter, None)
        return positions

    @staticmethod
    def to_order_status(status: str):
        if status == 'NEW':
            return OrderStatus.OPEN
        elif status == 'PARTIALLY_FILLED':
            return OrderStatus.PARTIALLY_FILLED
        elif status == 'FILLED':
            return OrderStatus.FILLED
        elif status in ('CANCELED', 'REJECTED'):
            return OrderStatus.CANCELED
        elif status in 'EXPIRED':
            return OrderStatus.EXPIRED
        raise ValueError(f'invalid order status: {status}')

    def parse_order_response(self, response: dict) -> FuturesOrder:
        return FuturesOrder(symbol=self.to_blankly_symbol(response['symbol']),
                            id=int(response['orderId']),
                            status=self.to_order_status(response['status']),
                            size=float(response['origQty']),
                            type=OrderType(response['type'].lower()),
                            contract_type=ContractType.PERPETUAL,
                            side=Side(response['side'].lower()),
                            position=PositionMode(
                                response['positionSide'].lower()),
                            time_in_force=TimeInForce(response['timeInForce']),
                            price=float(response['cumQuote']),
                            limit_price=float(response['price']),
                            response=response,
                            interface=self)

    @utils.order_protection
    def market_order(self,
                     symbol: str,
                     side: Side,
                     size: float,
                     position: PositionMode = PositionMode.BOTH,
                     reduce_only: bool = False) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        params = {
            'type': 'MARKET',
            'symbol': symbol,
            'side': side.upper(),
            'quantity': size,
            'positionSide': position.upper(),
            'reduceOnly': reduce_only
        }
        response = self.calls.futures_create_order(**params)

        return self.parse_order_response(response)

    @utils.order_protection
    def limit_order(
            self,
            symbol: str,
            side: Side,
            price: float,
            size: float,
            position: PositionMode = PositionMode.BOTH,
            reduce_only: bool = False,
            time_in_force: TimeInForce = TimeInForce.GTC) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        params = {
            'type': 'LIMIT',
            'symbol': symbol,
            'side': side.upper(),
            'price': price,
            'quantity': size,
            'positionSide': position.upper(),
            'reduceOnly': reduce_only,
            'timeInForce': time_in_force.value
        }
        response = self.calls.futures_create_order(**params)

        return self.parse_order_response(response)

    def take_profit_order(
            self,
            symbol: str,
            side: Side,
            price: float,
            size: float,
            position: PositionMode = PositionMode.BOTH,
            time_in_force: TimeInForce = TimeInForce.GTC) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        params = {
            'type': 'TAKE_PROFIT',
            'symbol': symbol,
            'side': side.upper(),
            'price': price,
            'stopPrice': price,  # TODO allow set stop price
            'quantity': size,
            'positionSide': position.upper(),
            'timeInForce': time_in_force.value
        }
        response = self.calls.futures_create_order(**params)

        return self.parse_order_response(response)

    @utils.order_protection
    def stop_loss_order(
            self,
            symbol: str,
            side: Side,
            price: float,
            size: float,
            position: PositionMode = PositionMode.BOTH,
            time_in_force: TimeInForce = TimeInForce.GTC) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        params = {
            'type': 'STOP',
            'symbol': symbol,
            'side': side.upper(),
            'price': price,
            'stopPrice': price,  # TODO allow set stop price
            'quantity': size,
            'positionSide': position.upper(),
            'timeInForce': time_in_force.value
        }
        response = self.calls.futures_create_order(**params)

        return self.parse_order_response(response)

    @utils.order_protection
    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        # this library method is broken for some reason 2021-02-25
        res = self.calls.futures_cancel_order(symbol=symbol, orderId=order_id)
        return self.parse_order_response(res)

    def get_open_orders(self, symbol: str = None) -> list:
        if symbol:
            symbol = self.to_exchange_symbol(symbol)
            orders = self.calls.futures_get_open_orders(symbol=symbol)
        else:
            orders = self.calls.futures_get_open_orders()
        return [self.parse_order_response(order) for order in orders]

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        res = self.calls.futures_get_order(symbol=symbol, orderId=order_id)
        return self.parse_order_response(res)

    def get_price(self, symbol: str) -> float:
        symbol = self.to_exchange_symbol(symbol)
        return float(self.calls.futures_mark_price(symbol=symbol)['markPrice'])

    def get_fees(self) -> dict:
        # https://www.binance.com/en/blog/futures/trade-crypto-futures-how-much-does-it-cost-421499824684902239
        tier = int(self.calls.futures_account()['feeTier'])
        maker, taker = BINANCE_FUTURES_FEES[tier]
        return {'maker': maker, 'taker': taker}

    def get_maker_fee(self) -> float:
        return self.get_fees()['maker']

    def get_taker_fee(self) -> float:
        return self.get_fees()['taker']

    @property
    def account(self) -> dict:
        return self.get_account()

    @property
    def orders(self) -> list:
        return self.get_open_orders()

    def get_product_history(self, symbol, epoch_start, epoch_stop,
                            resolution) -> pd.DataFrame:
        # reuse impl from SPOT interface, it's the same thing
        return BinanceInterface._binance_get_product_history(self.calls, symbol, epoch_start, epoch_stop, resolution)

    def get_funding_rate_history(self, symbol: str, epoch_start: int,
                                 epoch_stop: int) -> list:
        if self.calls.testnet:
            # testnet api is incredibly stupid and has cost me several hours of my life
            resolution = self.get_funding_rate_resolution()
            start = int(epoch_start)
            end = int(epoch_stop)
            start = start - (start % resolution) + resolution
            end = end - (end % resolution) + resolution
            return [{'rate': 0.0001, 'time': t}
                    for t in range(start, end + 1, resolution)]

        history = []
        window = int(epoch_start)

        response = True
        while response:
            response = self.calls.futures_funding_rate(
                symbol=symbol,
                startTime=window,
                limit=1000)
            # very stinky ^^

            history.extend({'rate': float(e['fundingRate']),
                            'time': e['fundingTime'] // 1000}
                           for e in response)

            if history:
                # the (testnet) api is stupid and sometimes gives us times we don't want
                if history[0]['time'] < window:
                    break
                window = history[-1]['time'] + 1
                if epoch_stop < window:
                    break
        history.sort(key=itemgetter('time'))
        while history and epoch_stop < history[-1]['time']:
            history.pop()
        while history and history[0]['time'] < epoch_start:
            history.pop(0)
        return history

    def get_funding_rate_resolution(self) -> int:
        return time_builder.build_hour() * 8  # 8 hours

    def get_funding_rate(self, symbol: str):
        response = self.calls.futures_mark_price(symbol=symbol)
        return response['nextFundingTime'], response['lastFundingRate']


