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
from copy import deepcopy


class FuturesPaperTradeInterface(FuturesExchangeInterface, BacktestingWrapper):
    interface: FuturesExchangeInterface
    paper_account: dict
    paper_positions: dict
    next_fund: int

    _funding_rate_cache: list

    # mapping of contract names -> quote currency used
    # BTC-PERP -> USDT/USD
    _quote_map: dict

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

    def add_asset(self, asset):
        if asset not in self.traded_assets:
            self.traded_assets.append(asset)

    def add_symbol(self, symbol):
        base, quote = symbol.split('-')
        contract_name = base + '-PERP'
        self._quote_map[contract_name] = quote
        self.add_asset(contract_name)
        self.add_asset(quote)

    def __init__(self, exchange_name: str, interface: FuturesExchangeInterface, account_values: dict = None):
        super().__init__(exchange_name, interface.calls)
        BacktestingWrapper.__init__(self)
        self.interface = interface
        self.next_fund = 0

        self._placed_orders = {}
        self._executed_orders = {}
        self._canceled_orders = {}
        self._funds_held = {}
        self._quote_map = {}
        self._funding_rate_cache = []

        # same functionality as 'real' FuturesExchangeInterface's
        self.paper_account = defaultdict(lambda: {'available': 0, 'hold': 0})
        self.paper_positions = {}
        self.traded_assets = []
        self.margin_types = {}

        self.init_exchange()
        self.override_local_account(account_values or {})

    def init_exchange(self):
        self.interface.init_exchange()

    @functools.lru_cache(None)
    def get_products(self, symbol: str = None) -> dict:
        return self.interface.get_products(symbol)

    def get_account(self, symbol: str = None) -> dict:
        acc = deepcopy(self.paper_account)
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

    def limit_order(self, symbol: str, side: Side, price: float, size: float, position: PositionMode = PositionMode.BOTH,
                    reduce_only: bool = False, time_in_force: TimeInForce = None) -> FuturesOrder:
        return self._place_order(OrderType.LIMIT, symbol, side, size, price, position, reduce_only)

    def take_profit(self, symbol: str, side: Side, price: float, size: float,
                    position: PositionMode = PositionMode.BOTH) -> FuturesOrder:
        return self._place_order(OrderType.TAKE_PROFIT, symbol, side, size, price, position)

    def stop_loss(self, symbol: str, side: Side, price: float, size: float,
                  position: PositionMode = PositionMode.BOTH) -> FuturesOrder:
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

    def set_hedge_mode(self, hedge_mode: HedgeMode):
        if hedge_mode == HedgeMode.HEDGE:
            raise ValueError('Hedge mode not supported')

    def get_hedge_mode(self):
        return HedgeMode.ONEWAY

    def set_leverage(self, leverage: int, symbol: str = None):
        if leverage != 1:
            raise ValueError('paper trading with leverage not supported')

    def get_leverage(self, symbol: str = None) -> float:
        return 1

    def set_margin_type(self, symbol: str, type: MarginType):
        self.margin_types[symbol] = type

    def get_margin_type(self, symbol: str) -> MarginType:
        return self.margin_types.get(symbol, MarginType.CROSSED)

    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        try:
            order = self._placed_orders[order_id][1]
            del self._placed_orders[order_id]
            assert order.symbol == symbol
            return dataclasses.replace(order, status=OrderStatus.CANCELED)
        except KeyError:
            raise Exception('order not found')

    def get_open_orders(self, symbol: str = None) -> List[FuturesOrder]:
        return [dataclasses.replace(o) for o in self._placed_orders]

    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
        try:
            order = self._placed_orders[order_id][1]
            assert order.symbol == symbol
            return dataclasses.replace(order, status=OrderStatus.CANCELED)
        except KeyError:
            raise Exception('order not found')

    def get_funding_rate(self, symbol: str):
        if self.backtesting:
            return self.get_backtesting_funding_rate(symbol)
        else:
            return self.interface.get_funding_rate(symbol)

    def get_backtesting_funding_rate(self, symbol: str):
        # check if cache needs to be refreshed
        # TODO this all need to be moved into events framework once that's done
        time = self.time()
        if not self._funding_rate_cache or self._funding_rate_cache[-1]['time'] < time:
            self._funding_rate_cache = self.get_funding_rate_history(symbol, time, None)
        for i, o in self._funding_rate_cache[:-1].enumerate():
            if o['time'] < time:
                last = o['rate']
                next = self._funding_rate_cache[i+1]['time']
                return last, next
        print(f'failed to download funding rate at time {time}')
        return 0.0001, time + (time % self.get_funding_rate_resolution())


    def get_price(self, symbol: str) -> float:
        if symbol.endswith('-PERP'):
            quote = self._quote_map[symbol]
            symbol = symbol.split('-')[0] + '-' + quote
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

    def check_funding_rate(self, symbol):
        if not self.next_fund:
            last, self.next_fund = self.get_funding_rate(symbol)
            return
        if self.next_fund < self.time():
            fund, self.next_fund = self.get_funding_rate(symbol)
            # fund!
            position_size = self.paper_positions[symbol]['size']
            if not position_size:
                return
            value = position_size * self.get_price(symbol)
            m = -1 if (position_size > 0) == ()



    def evaluate_limits(self):
        # TODO this needs to be part of the event stuff once that's fleshed out
        symbols = {position['symbol'] for position in self.paper_positions}
        for symbol in symbols:
            self.check_funding_rate(symbol)

        # TODO reduce_only on limit order "technically" broken
        for id, order_data in list(self._placed_orders.items()):
            is_closing, order = order_data
            order: FuturesOrder

            if not self.should_run_order(order):
                continue

            base, quote = order.symbol.split('-')

            asset_price = order.limit_price or self.get_price(order.symbol)
            # if we held funds for the order, use those orelse just default to current price * ordersize
            held_curr, notional = self._funds_held.pop(id, (quote, asset_price * order.size))

            assert held_curr == quote

            # copy order to _executed_orders
            del self._placed_orders[id]
            self._executed_orders[id] = dataclasses.replace(order, status=OrderStatus.FILLED, price=notional)

            position_size = (self.get_position(order.symbol) or {'size': 0})['size']
            size_diff = order.size * (1 if order.side == Side.BUY else -1)

            # we sold off our position
            if is_closing:
                self.paper_account[quote]['available'] += notional
            else:
                self.paper_account[quote]['hold'] -= notional

            # this overwrites but it's fine, we don't need to update
            new_position = position_size + size_diff
            if new_position:
                self.paper_positions[order.symbol] = {
                    'symbol': order.symbol,
                    'size': new_position,
                    'position': PositionMode.BOTH,
                    'contract_type': ContractType.PERPETUAL,
                    'exchange_specific': {}
                }
            else:
                del self.paper_positions[order.symbol]
            self.paper_account[base + '-PERP']['available'] = new_position
            pass

    def _place_order(self, type: OrderType, symbol: str, side: Side, size: float, limit_price: float = 0,
                     positionMode: PositionMode = PositionMode.BOTH, reduce_only: bool = False,
                     time_in_force: TimeInForce = TimeInForce.GTC) -> FuturesOrder:
        self.add_symbol(symbol)
        product = self.get_products(symbol)

        if not product:
            raise ValueError(f'invalid symbol {symbol}')

        if positionMode != PositionMode.BOTH:
            raise ValueError(f'only PositionMode.BOTH is supported for paper trading at this time')

        if size <= 0:
            raise ValueError('cannot place empty order')

        if limit_price < 0 or (limit_price == 0 and type != OrderType.MARKET):
            raise ValueError('invalid limit price')

        # place funds on hold
        if type == OrderType.MARKET:
            price = self.get_price(symbol)
        elif reduce_only:
            raise ValueError('reduce_only only supported for market order')
        else:
            price = limit_price

        position = self.get_position(symbol)
        # close position if we are selling from >0 position or buying <0 position
        # no position == we are never closing
        is_closing = self.is_closing_position(position, side)
        if not position and reduce_only:
            raise Exception('reduce_only set to True but there is no position to reduce')

        if reduce_only and not is_closing:
            raise Exception(f'reduce_only set to True but order side ({side}) is opening or growing position')

        if reduce_only:
            size = min(size, abs(position['size']))

        if is_closing and size > abs(position['size']):
            # we need to close position and then buy/sell extra w/ the extra funds
            # this is weird behavior but it's what binance futures does
            # for now raise exception in backtesting, nobody is going to do this anyways
            # and the workaround is simple, just close your position first
            raise Exception('order size is greater than position, close your position first and then place order')

        base, quote = symbol.split('-')
        acc = self.paper_account[quote]

        fee = self.get_taker_fee()
        if is_closing:
            funds = (price * size) * (1 - fee)
        else:
            funds = (price * size) * (1 + fee)

        order_id = self.gen_order_id()
        if not is_closing:
            if acc['available'] < funds:
                raise Exception('not enough funds')

            acc['available'] -= funds
            acc['hold'] += funds
            self._funds_held[order_id] = (quote, funds)

        order = FuturesOrder(symbol=symbol, id=order_id, size=size, status=OrderStatus.OPEN, type=type,
                             contract_type=ContractType.PERPETUAL, side=side, position=PositionMode.BOTH,
                             limit_price=limit_price,
                             price=0, time_in_force=TimeInForce.GTC, response={}, interface=self.interface)
        self._placed_orders[order_id] = (is_closing, order)

        self.evaluate_limits()

        return order

    def is_closing_position(self, position, side):
        if not position or position['size'] == 0:
            return False
        if (position['size'] > 0) == (side == Side.SELL):
            return True
        return False

    def gen_order_id(self):
        return random.randrange(10 ** 4, 10 ** 5)

    @functools.lru_cache(None)
    def get_maker_fee(self) -> float:
        return self.interface.get_maker_fee()

    @functools.lru_cache(None)
    def get_taker_fee(self) -> float:
        return self.interface.get_taker_fee()
