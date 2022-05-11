from typing import Union

from blankly.enums import ContractType, PositionMode, TimeInForce, Side, OrderStatus, OrderType
from blankly.exchanges.interfaces.paper_trade.paper_trade import PaperTrade
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro import CoinbasePro
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.okx.okx import Okx
from blankly.exchanges.interfaces.kucoin.kucoin import Kucoin
from blankly.exchanges.interfaces.binance.binance import Binance
from blankly.exchanges.interfaces.alpaca.alpaca import Alpaca
from blankly.exchanges.interfaces.oanda.oanda import Oanda
from blankly.exchanges.interfaces.ftx.ftx import FTX
from blankly.exchanges.abc_base_exchange import ABCBaseExchange
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.interfaces.binance_futures.binance_futures import BinanceFutures
from blankly.exchanges.interfaces.ftx_futures.ftx_futures import FTXFutures
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.interfaces.paper_trade.futures.futures_paper_trade_interface import FuturesPaperTradeInterface
from blankly.exchanges.interfaces.paper_trade.paper_trade_interface import PaperTradeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils import utils

import time
import functools
import os

import pytest
from _pytest.python import Metafunc
from _pytest.python_api import approx

from contextlib import contextmanager

# futures exchanges
binance_futures = BinanceFutures(keys_path="./tests/config/keys.json",
                                 preferences_path="./tests/config/settings.json",
                                 portfolio_name="Futures Test Key")
ftx_futures = FTXFutures(keys_path="./tests/config/keys.json",
                         preferences_path="./tests/config/settings.json",
                         portfolio_name="Dotcom Test Account")

# spot exchanges
coinbase_pro = CoinbasePro(portfolio_name="Sandbox Portfolio",
                           keys_path='./tests/config/keys.json',
                           settings_path="./tests/config/settings.json")
okx = Okx(portfolio_name="okx sandbox portfolio",
          keys_path='./tests/config/keys.json',
          settings_path="./tests/config/settings.json")
kucoin = Kucoin(portfolio_name="KC Sandbox Portfolio",
                keys_path='./tests/config/keys.json',
                settings_path="./tests/config/settings.json")
binance = Binance(portfolio_name="Spot Test Key",
                  keys_path='./tests/config/keys.json',
                  settings_path="./tests/config/settings.json")
alpaca = Alpaca(portfolio_name="alpaca test portfolio",
                keys_path='./tests/config/keys.json',
                settings_path="./tests/config/settings.json")
oanda = Oanda(portfolio_name="oanda test portfolio",
              keys_path='./tests/config/keys.json',
              settings_path="./tests/config/settings.json")
ftx = FTX(portfolio_name="Main Account",
          keys_path='./tests/config/keys.json',
          settings_path="./tests/config/settings.json")

FUTURES_EXCHANGES = [
    FuturesPaperTradeInterface(binance_futures.get_type() + '_paper_trade', binance_futures.interface, {'USDT': 1000}),
    binance_futures,
    ftx_futures,
]
SPOT_EXCHANGES = [
    # PaperTradeInterface deferring to the subinterface get_exchange_type causes problems...
    # TODO ?
    PaperTrade(coinbase_pro, {'USD': 1000}),

    # CoinbasePro testnet *sucks*. Trading on it is always fkn broken and they list like 3 symbols.
    # It breaks all the tests.
    # coinbase_pro,

    okx,
    kucoin,
    binance,
    alpaca,
    oanda,
    ftx
]

for exchange in FUTURES_EXCHANGES + SPOT_EXCHANGES:
    # override auto trunc for new tests
    # old tests use the default if auto_truncate is not set, which is False
    exchange.interface.user_preferences['settings']['auto_truncate'] = True


def get_symbols(exchange: ABCBaseExchangeInterface):
    exchange_type = exchange.get_exchange_type()

    # crypto exchanges that use USD
    if exchange_type.startswith('coinbase') \
            or exchange_type.startswith('ftx'):
        return ['BTC-USD']

    # forex
    if exchange_type.startswith('oanda'):
        return ['EUR-USD', 'GBP/CAD']

    # stonks
    if exchange_type.startswith('alpaca'):
        return ['AAPL', 'MSFT']

    # everything else uses USDT
    return ['ETH-USDT', 'BCH-USDT']


def homogeneity_testing(func=None, check_values: bool = False):
    # allow using without arguments
    # this trick brought to you by Python Cookbook
    if func is None:
        return functools.partial(homogeneity_testing, values=check_values)

    results = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        test_name = os.environ.get('PYTEST_CURRENT_TEST')
        test_name = test_name[test_name.find('[') + 1:test_name.find(']')]
        result = func(*args, **kwargs)
        compare_results(results, result, check_values)
        results[test_name] = result
        return result

    return wrapper


def compare_results(previous_outputs: dict, result, check_values: bool):
    for prev_name, prev_results in previous_outputs.items():
        compare_values(prev_name, prev_results, result, check_values)


def compare_values(other_name, other, this, check_values: bool):
    assert type(this) == type(
        other
    ), f'comparing to {other_name}: types do not match. this={this} other={other}'
    # gapped by python 3.7
    # ), f'comparing to {other_name}: types do not match. {this=} {other=}'
    if isinstance(this, list):
        if this and other:
            for val in this[1:]:  # check for self-homogenity
                compare_values('self', val, this[0], check_values)
            for val in other:
                compare_values(other_name, val, this[0], check_values)
    if isinstance(other, dict):
        other.pop('exchange_specific', None)
        this.pop('exchange_specific', None)
        assert this.keys() == other.keys(
        ), f'comparing to {other_name}: dict keys do not match. ' \
           f'symmetric difference: {set(this.keys()).symmetric_difference(other.keys())}'
        for key in other:
            compare_values(other_name, other[key], this[key], check_values)
    elif check_values:
        assert this == other, f'comparing to {other_name}: values are not equal.'


def wait_till_filled(interface: ABCBaseExchangeInterface, order: Union[FuturesOrder, MarketOrder]):
    if isinstance(interface, ExchangeInterface):
        # don't bother, the lack of 'real' order statuses makes this too much of a pain
        time.sleep(1)
        return interface.get_order(order.get_symbol(), order.get_id())

    retries = 0
    res = interface.get_order(order.symbol, order.id)
    while res.status != OrderStatus.FILLED:
        if retries > 2:
            pytest.fail(f"order was not filled in time. status: {res.status}")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(res.symbol, order.id)
    return res


def place_order(interface: ABCBaseExchangeInterface, symbol: str, side: Side, funds: int, reduce_only: bool = False):
    if isinstance(interface, FuturesExchangeInterface):
        product = interface.get_products(symbol)
        price = interface.get_price(symbol)
        precision = product['size_precision']
    else:
        product = next(p for p in interface.get_products() if p['symbol'] == symbol)
        price = interface.get_price(symbol)
        precision = utils.increment_to_precision(product['base_increment'])
    order_size = utils.trunc(funds / price, precision)

    if isinstance(interface, FuturesExchangeInterface):
        order = interface.market_order(symbol, side, order_size, reduce_only=reduce_only)
        assert order.symbol == symbol
        assert 0 <= order.id
        assert order.status in (OrderStatus.OPEN, OrderStatus.FILLED)
        assert order.type == OrderType.MARKET
        assert order.contract_type == ContractType.PERPETUAL
        assert order.side == side
        assert order.limit_price == 0
        assert order.position == PositionMode.BOTH
        assert order.time_in_force == TimeInForce.GTC
    else:
        order = interface.market_order(symbol, side, order_size)
        assert order.get_symbol() == symbol
        # TODO these are not properly homogenized for spot markets
        assert order.get_status()['status'].lower() in ('new', 'open', 'filled', 'done')
        assert order.get_type().lower() == OrderType.MARKET
        assert order.get_size() == approx(order_size)
        assert order.get_side().lower() == side

    res = wait_till_filled(interface, order)

    if isinstance(interface, FuturesExchangeInterface):
        assert res.status == OrderStatus.FILLED
    else:
        assert res.get_status()["status"].lower() in ('closed', 'filled')

    if isinstance(interface, FuturesExchangeInterface):
        if reduce_only:
            # 1% tolerance
            assert res.price <= price * order_size * 1.01
            assert res.size <= order_size * 1.01

            # set size equal so we can compare
            order.size = res.size
        else:
            assert res.price == approx(price * order_size, rel=0.01)
            assert res.size == approx(order_size)

        # set price, status equal so we can compare
        order.price = res.price
        order.status = res.status
        assert order == res
    else:
        assert res.get_price() == approx(price * order_size, rel=0.01)
        assert res.get_size() == approx(order_size, rel=0.01)

    return order


def sell(interface: ABCBaseExchangeInterface, symbol: str, funds: int = 20, reduce_only: bool = False):
    return place_order(interface, symbol, Side.SELL, funds, reduce_only)


def buy(interface: ABCBaseExchangeInterface, symbol: str, funds: int = 20, reduce_only: bool = False):
    return place_order(interface, symbol, Side.BUY, funds, reduce_only)


def close_all(futures_interface: FuturesExchangeInterface):
    for symbol in futures_interface.get_position():
        close_position(futures_interface, symbol)

    for order in futures_interface.get_open_orders():
        futures_interface.cancel_order(order.symbol, order.id)
    assert len(futures_interface.get_position()) == 0


def close_position(interface: ABCBaseExchange, symbol: str):
    """
    Exit position
    Args:
        interface: the interface to sell on
        symbol: the symbol to sell
    """
    if isinstance(interface, FuturesExchangeInterface):
        position = interface.get_position(symbol)
        if not position:
            return
        if position['size'] < 0:
            order = interface.market_order(symbol,
                                           Side.BUY,
                                           position['size'] * -2,
                                           reduce_only=True)
        elif position['size'] > 0:
            order = interface.market_order(symbol,
                                           Side.SELL,
                                           position['size'] * 2,
                                           reduce_only=True)
        else:
            pytest.fail('position size is zero')
        wait_till_filled(interface, order)
        assert interface.get_position(symbol) is None
    else:
        base = utils.get_base_asset(symbol)
        acc = interface.get_account()
        if base not in acc:
            return
        product = next(p for p in interface.get_products() if p['symbol'] == symbol)
        increment = product['base_increment']
        precision = utils.increment_to_precision(increment)
        position = utils.trunc(acc[base]['available'], precision)
        if 0 < position:
            order = interface.market_order(symbol, 'sell', position)
            wait_till_filled(interface, order)
            assert interface.get_account(base)['available'] == approx(0)


@contextmanager
def cancelling_order(interface: ABCBaseExchangeInterface, symbol: str):
    """
    Context manager for placing and cancelling a limit order from within a test.
    Useful for testing paths that require active orders.
    Args:
        interface: The interface to place an order on
        symbol: The symbol to buy

    Returns: The order object as returned from the interface
    """
    product = interface.get_products(symbol)
    price = interface.get_price(symbol)

    # place our limit order
    if isinstance(interface, FuturesExchangeInterface):
        order_size = utils.trunc(100 / price, product['size_precision'])
        limit_price = utils.trunc(price * 0.90, product['price_precision'])
        order = interface.limit_order(symbol, Side.BUY, limit_price, order_size)
        assert order.symbol == symbol
        assert 0 <= order.id
        assert order.size == approx(order_size)
        assert order.status == OrderStatus.OPEN
        assert order.type == OrderType.LIMIT
        assert order.contract_type == ContractType.PERPETUAL
        assert order.side == Side.BUY
        assert order.position == PositionMode.BOTH
        assert order.limit_price == approx(limit_price)
        assert order.time_in_force == TimeInForce.GTC
    else:
        order_size = utils.trunc(100 / price, utils.increment_to_precision(product['base_increment']))
        limit_price = utils.trunc(price * 0.90, 2)  # 2 should be fine? we don't have quote asset increment here.
        order = interface.limit_order(symbol, 'buy', limit_price, order_size)
        assert order.get_symbol() == symbol
        # TODO these are not properly homogenized for spot markets
        assert order.get_status()['status'].lower() in ('new', 'open', 'filled')
        assert order.get_type().lower() == OrderType.MARKET
        assert order.get_size() == approx(order_size)
        assert order.get_side().lower() == Side.BUY
        assert order.get_price() == approx(limit_price)

    yield order

    res = interface.cancel_order(symbol, order.id)

    if isinstance(interface, FuturesExchangeInterface):
        assert res.status == OrderStatus.CANCELED

        assert order != res
        res.status = OrderStatus.OPEN
        assert order == res
