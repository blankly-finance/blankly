import dataclasses
import functools
import random
from collections import defaultdict
from typing import List, Optional

from blankly.enums import MarginType, HedgeMode, PositionMode, Side, TimeInForce, ContractType, OrderStatus, OrderType
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.interfaces.paper_trade.backtesting_wrapper import BacktestingWrapper
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from blankly.utils import utils as utils


class FuturesPaperTradeInterface(FuturesExchangeInterface, BacktestingWrapper):
    interface: FuturesExchangeInterface
    paper_account: dict
    paper_positions: dict

    # orders
    _placed_orders: dict
    _executed_orders: dict
    _canceled_orders: dict
    _funds_held: dict

    # not used, just for funsies
    margin_types: dict

    # needed for backtesting_wrapper:
    traded_assets: list

    @property
    def paper_trade_orders(self) -> list:
        return []

    @property
    def executed_orders(self) -> list:
        return []

    @property
    def canceled_orders(self) -> list:
        return []

    @property
    def market_order_execution_details(self) -> list:
        return []

    def add_asset(self, symbol):
        base, quote = symbol.split('-')
        if base not in self.traded_assets:
            self.traded_assets.append(base)
        if quote not in self.traded_assets:
            self.traded_assets.append(quote)

    def __init__(self, exchange_name: str, interface: FuturesExchangeInterface, account_values: dict = None):
        super().__init__(exchange_name, interface.calls)
        BacktestingWrapper.__init__(self)
        self.interface = interface

        self._placed_orders = {}
        self._executed_orders = {}
        self._canceled_orders = {}
        self._funds_held = {}

        # same functionality as 'real' FuturesExchangeInterface's
        self.paper_account = defaultdict(lambda: {'available': 0, 'hold': 0})
        self.paper_positions = {}
        self.traded_assets = []
        self.margin_types = {}

        self.init_exchange()
        self.override_local_account(account_values or {})

    def init_exchange(self):
        self.interface.init_exchange()

    def get_products(self, symbol: str = None) -> dict:
        return self.interface.get_products(symbol)

    def get_account(self, symbol: str = None) -> dict:
        acc = self.paper_account
        if symbol:
            try:
                return acc[symbol]
            except KeyError as e:
                if self.backtesting:
                    raise KeyError(
                        "Symbol not found. This can be caused by an invalid quote currency in backtest.json.", e)
                else:
                    raise KeyError("Symbol not found.", e)
        return acc

    def get_position(self, symbol: str = None) -> Optional[dict]:
        if symbol:
            return self.paper_positions.get(symbol, None)
        return self.paper_positions

    def market_order(self, symbol: str, side: Side, size: float, position: PositionMode = PositionMode.BOTH,
                     reduce_only: bool = False) -> FuturesOrder:
        return self._place_order(OrderType.MARKET, symbol, side, size, 0, position, reduce_only)

    def limit_order(self, symbol: str, side: Side, price: float, size: float, position: PositionMode = None,
                    reduce_only: bool = None, time_in_force: TimeInForce = None) -> FuturesOrder:
        return self._place_order(OrderType.LIMIT, symbol, side, size, price, position, reduce_only)

    def take_profit(self, symbol: str, side: Side, price: float, size: float,
                    position: PositionMode = None) -> FuturesOrder:
        return self._place_order(OrderType.TAKE_PROFIT, symbol, side, size, price, position)

    def stop_loss(self, symbol: str, side: Side, price: float, size: float,
                  position: PositionMode = None) -> FuturesOrder:
        return self._place_order(OrderType.STOP, symbol, side, size, price, position)

    def should_run_order(self, order):
        price = self.get_price(order.symbol)

        if order.type == OrderType.MARKET:
            return True

        if order.type == OrderType.LIMIT:
            if order.side == Side.BUY:
                return price <= order.limit_price
            elif order.side == Side.SELL:
                return price >= order.limit_price

        raise Exception(f'invalid order')

    def evaluate_limits(self):
        # TODO reduce_only on limit order "technically" broken
        for id, order in self._placed_orders.items():
            order: FuturesOrder

            if not self.should_run_order(order):
                continue

            curr, funds = self._funds_held.pop(id)
            self.paper_account[curr]['hold'] -= funds

            del self._placed_orders[id]
            order = dataclasses.replace(order)  # create copy of order
            self._executed_orders[id] = order
            order.price = funds

            size = self.paper_positions.get(order.symbol, {'size': 0})['size']
            self.paper_positions[order.symbol] = {
                'symbol': order.symbol,
                'size': size + order.size,
                'position': PositionMode.BOTH,
                'contract_type': ContractType.PERPETUAL,
                'exchange_specific': {}
            }

    def set_hedge_mode(self, hedge_mode: HedgeMode):
        if hedge_mode == HedgeMode.HEDGE:
            raise ValueError('Hedge mode not supported')

    def get_hedge_mode(self):
        return HedgeMode.ONEWAY

    def set_leverage(self, leverage: int, symbol: str = None):
        if leverage != 1:
            raise ValueError('paper trading with leverage not supported')

    def get_leverage(self, symbol: str = None) -> float:
        raise NotImplementedError

    def set_margin_type(self, symbol: str, type: MarginType):
        self.margin_types[symbol] = type

    def get_margin_type(self, symbol: str) -> MarginType:
        return self.margin_types.get(symbol, MarginType.CROSSED)

    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        raise NotImplementedError

    def get_open_orders(self, symbol: str = None) -> List[FuturesOrder]:
        raise NotImplementedError

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        raise NotImplementedError

    def get_price(self, symbol: str) -> float:
        if self.backtesting:
            return self.get_backtesting_price(symbol)
        else:
            return self.interface.get_price(symbol)

    def get_funding_rate_history(self, symbol: str, epoch_start: int, epoch_stop: int) -> list:
        return self.interface.get_funding_rate_history(symbol, epoch_start, epoch_stop)

    def get_funding_rate_resolution(self) -> int:
        return self.interface.get_funding_rate_resolution()

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        return self.interface.get_product_history(symbol, epoch_start, epoch_stop, resolution)

    def evaluate_traded_account_assets(self):
        pass

    def override_local_account(self, value_dictionary: dict):
        # if python3.9 we could use the new dict update operator here :(
        self.paper_account.update({
            asset: {'available': value, 'hold': 0} for asset, value in value_dictionary.items()
        })

        self.traded_assets.extend(value_dictionary.keys())

    def _place_order(self, type: OrderType, symbol: str, side: Side, size: float, limit_price: float = 0,
                     position: PositionMode = PositionMode.BOTH, reduce_only: bool = False,
                     time_in_force: TimeInForce = TimeInForce.GTC) -> FuturesOrder:
        product = self.get_products(symbol)

        if not product:
            raise ValueError(f'invalid symbol {symbol}')

        if position != PositionMode.BOTH:
            raise ValueError(f'only PositionMode.BOTH is supported for paper trading at this time')

        if size <= 0:
            raise ValueError('cannot place empty order')

        if limit_price < 0 or (limit_price == 0 and type != OrderType.MARKET):
            raise ValueError('invalid limit price')

        # place funds on hold
        if type == OrderType.MARKET:
            price = self.get_price(symbol)
        else:
            price = limit_price
        funds = (price * size) * self.get_taker_fee()
        base, quote = symbol.split('-')
        acc = self.paper_account[quote]
        if acc['available'] < funds:
            raise Exception('not enough funds')

        acc['available'] -= funds
        acc['hold'] += funds

        # place order
        order_id = self.gen_order_id()
        order = FuturesOrder(symbol=symbol, id=order_id, size=size, status=OrderStatus.OPEN, type=type,
                             contract_type=ContractType.PERPETUAL, side=side, position=PositionMode.BOTH,
                             price=limit_price,
                             limit_price=0, time_in_force=TimeInForce.GTC, response={}, interface=self.interface)
        self._placed_orders[order_id] = order
        self._funds_held[order_id] = (quote, funds)

    def gen_order_id(self):
        return random.randrange(10 ** 4, 10 ** 5)
