"""
    FTX Futures impl of FuturesExchangeInterface.
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

import operator
from typing import Optional

from blankly.enums import MarginType, HedgeMode, Side, PositionMode, TimeInForce, ContractType, OrderStatus, OrderType
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from blankly.utils import utils, time_builder
import datetime
import math


class FTXFuturesInterface(FuturesExchangeInterface):
    calls: FTXAPI

    @staticmethod
    def to_exchange_symbol(symbol: str):
        base_asset, quote_asset = symbol.split('-')
        if quote_asset != 'USD':
            raise ValueError('invalid symbol')
        return base_asset + '-PERP'  # only perpetual contracts right now

    @staticmethod
    def to_blankly_symbol(symbol: str):
        base_asset, contract_type = symbol.split('-', 1)
        if contract_type != 'PERP':
            raise ValueError(
                'invalid symbol -- blankly only supports perpetual contracts')
        return base_asset + '-USD'

    @staticmethod
    def parse_timestamp(time: str) -> int:
        return int(datetime.datetime.fromisoformat(time).timestamp())

    @staticmethod
    def to_order_status(status: str, cancel: bool = False) -> OrderStatus:
        if status in ('new', 'open'):
            return OrderStatus.OPEN
        elif status == 'closed':
            if cancel:
                return OrderStatus.CANCELED
            else:
                return OrderStatus.FILLED
        raise ValueError(f'invalid order status: {status}')

    @staticmethod
    def to_order_type(type: str) -> OrderType:
        if type == 'market':
            return OrderType.MARKET
        elif type == 'limit':
            return OrderType.LIMIT
        elif type == 'takeProfit':
            return OrderType.TAKE_PROFIT
        elif type == 'stop':
            return OrderType.STOP
        raise ValueError(f'invalid order type: {type}')

    def parse_order_response(self,
                             response: dict,
                             cancel: bool = False) -> FuturesOrder:
        return FuturesOrder(
            symbol=response['future'],
            id=int(response['id']),
            status=self.to_order_status(response['status'], cancel),
            size=float(response['size']),
            type=self.to_order_type(response['type']),
            contract_type=ContractType.PERPETUAL,
            side=Side(response['side']),
            position=PositionMode.BOTH,
            price=float(response['avgFillPrice']),
            limit_price=float(response['price']),
            time_in_force=TimeInForce.IOC
            if response['ioc'] else TimeInForce.GTC,
            response=response,
            interface=self)

    def init_exchange(self):
        # will throw exception if our api key is stinky
        self.calls.get_account_info()

    def get_products(self, filter: str = None) -> dict:
        res = self.calls.list_futures()
        products = {}
        for prod in res:
            if '-PERP' not in prod['name']:
                continue  # only perpetual contracts for now
            symbol = prod['underlying'] + '-USD'
            products[symbol] = {
                'symbol': symbol,
                'base_asset': prod['underlying'],
                'quote_asset': 'USD',
                'contract_type': ContractType.PERPETUAL,
                'price_precision': utils.increment_to_precision(
                    prod['priceIncrement']),
                'size_precision': utils.increment_to_precision(
                    prod['sizeIncrement']),
                'exchange_specific': prod
            }
        if filter:
            return products[filter]
        return products

    def get_account(self, filter: str = None) -> dict:
        balances = self.calls.get_balances()
        coins = self.calls.get_coins()
        accounts = {
            coin['id']: {
                'available': 0.0,
                'hold': 0.0,  # TODO
                'exchange_specific': coin
            }
            for coin in coins
        }

        for bal in balances:
            coin = bal['coin']
            accounts[coin].available = float(bal['free'])
            # merge into exchange_specific
            accounts[coin].exchange_specific = {
                **accounts[coin].exchange_specific,
                **bal
            }

        if filter:
            return accounts[filter]
        return accounts

    def get_position(self, filter: str = None) -> Optional[dict]:
        leverage = self.get_leverage()

        res = self.calls.get_positions()
        positions = {}
        for position in res:
            symbol = self.to_exchange_symbol(position['future'])
            size = float(position['netSize'])
            if size == 0:
                continue
            positions[symbol] = {
                'size': size,
                'position': PositionMode.BOTH,
                'contract_type': ContractType.PERPETUAL,
                'exchange_specific': position
            }

        if filter:
            return positions.get(filter, None)
        return positions

    def market_order(self,
                     symbol: str,
                     side: Side,
                     size: float,
                     position: PositionMode = PositionMode.BOTH,
                     reduce_only: bool = False) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        if position != PositionMode.BOTH:
            raise ValueError(
                f'position mode {position} not supported on FTX Futures')
        res = self.calls.place_order(symbol, side, None, size, 'market',
                                     reduce_only)
        return self.parse_order_response(res)

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
        if time_in_force == TimeInForce.GTC:
            ioc = False
        elif time_in_force == TimeInForce.IOC:
            ioc = True
        else:
            raise ValueError(
                f'time in force {time_in_force} not supported on FTX Futures')
        if position != PositionMode.BOTH:
            raise ValueError(
                f'position mode {position} not supported on FTX Futures')
        res = self.calls.place_order(symbol,
                                     side,
                                     price,
                                     size,
                                     'limit',
                                     reduce_only,
                                     ioc=ioc)
        return self.parse_order_response(res)

    def take_profit_order(
            self,
            symbol: str,
            side: Side,
            price: float,
            size: float,
            position: PositionMode = PositionMode.BOTH) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        if position != PositionMode.BOTH:
            raise ValueError(
                f'position mode {position} not supported on FTX Futures')
        res = self.calls.place_conditional_order(symbol,
                                                 side,
                                                 size,
                                                 'takeProfit',
                                                 trigger_price=price)
        return self.parse_order_response(res)

    def stop_loss_order(self,
                        symbol: str,
                        side: Side,
                        price: float,
                        size: float,
                        position: PositionMode = PositionMode.BOTH) -> FuturesOrder:
        symbol = self.to_exchange_symbol(symbol)
        if position != PositionMode.BOTH:
            raise ValueError(
                f'position mode {position} not supported on FTX Futures')
        res = self.calls.place_conditional_order(symbol,
                                                 side,
                                                 size,
                                                 'stop',
                                                 trigger_price=price)
        return self.parse_order_response(res)

    @utils.order_protection
    def set_hedge_mode(self, hedge_mode: HedgeMode):
        if hedge_mode == HedgeMode.HEDGE:
            raise Exception('HEDGE mode not supported on FTX Futures')
        pass  # FTX only has ONEWAY mode

    def get_hedge_mode(self):
        return HedgeMode.ONEWAY

    @utils.order_protection
    def set_leverage(self, leverage: float, symbol: str = None):
        if symbol:
            raise Exception(
                'FTX Futures does not allow setting leverage per symbol. Use interface.set_leverage(leverage) to set '
                'account-wide leverage instead. ')
        self.calls.change_account_leverage(leverage)

    def get_leverage(self, symbol: str = None) -> float:
        # doesn't matter if symbol passed or not, ftx leverage is same for all
        return self.calls.get_account_info()['leverage']

    @utils.order_protection
    def set_margin_type(self, symbol: str, type: MarginType):
        if type == MarginType.ISOLATED:
            raise Exception('isolated margin not supported on FTX Futures')
        pass

    def get_margin_type(self, symbol: str):
        return MarginType.CROSSED

    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        res = self.get_order(symbol, order_id)
        res.status = OrderStatus.CANCELED
        self.calls.cancel_order(str(order_id))
        return res

    def get_open_orders(self, symbol: str = None) -> list:
        return [
            self.parse_order_response(o) for o in self.calls.get_open_orders()
        ]

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        response = self.calls.get_order_by_id(str(order_id))
        symbol = self.to_exchange_symbol(symbol)
        if response['symbol'] != symbol:
            raise Exception(
                'response symbol did not match parameter -- this should never happen'
            )
        return self.parse_order_response(response)

    def get_price(self, symbol: str) -> float:
        symbol = self.to_exchange_symbol(symbol)
        return float(self.calls.get_future(symbol)['mark'])

    def get_funding_rate_history(self, symbol: str, epoch_start: int,
                                 epoch_stop: int) -> list:
        symbol = self.to_exchange_symbol(symbol)
        # TODO dedup binance_futures_exchange maybe?
        history = []
        resolution = self.get_funding_rate_resolution()
        limit = 500
        window_start = epoch_start
        window_end = epoch_start + limit * resolution

        response = True
        while response:
            response = self.calls.get_funding_rates(window_start, window_end,
                                                    symbol)

            history.extend({
                               'rate': float(e['rate']),
                               'time': self.parse_timestamp(e['time'])
                           } for e in response)

            if response:
                window_start = window_end
                window_end = min(epoch_stop, window_start + limit * resolution)

        return sorted(history, key=operator.itemgetter('time'))

    def get_funding_rate_resolution(self) -> int:
        return time_builder.build_hour()

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        raise NotImplementedError

    def get_maker_fee(self) -> float:
        raise NotImplementedError

    def get_taker_fee(self) -> float:
        raise NotImplementedError

    def get_funding_rate(self, symbol: str) -> float:
        raise NotImplementedError
