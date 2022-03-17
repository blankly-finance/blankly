import datetime
import time
import functools
import os

import pytest
from _pytest.python import Metafunc
from _pytest.python_api import approx

from blankly.enums import OrderStatus, Side, ContractType, OrderType, PositionMode, TimeInForce
from blankly.exchanges.interfaces.binance_futures.binance_futures import BinanceFutures
from blankly.exchanges.interfaces.ftx_futures.ftx_futures import FTXFutures
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder
from contextlib import contextmanager

from blankly.utils import utils

FUTURES_EXCHANGES = [
    BinanceFutures(keys_path="./tests/config/keys.json",
                   preferences_path="./tests/config/settings.json",
                   portfolio_name="Futures Test Key"),
    FTXFutures(keys_path="./tests/config/keys.json",
               preferences_path="./tests/config/settings.json",
               portfolio_name="Dotcom Test Account"),
]
SYMBOLS = {
    'ftx_futures': ['SOL-USD', 'ETH-USD'],
    'binance_futures': ['BCH-USDT', 'ETH-USDT']
}


def gen_id(arg):
    if isinstance(arg, FuturesExchange):
        return arg.get_type()
    elif isinstance(arg, FuturesExchangeInterface):
        return arg.get_exchange_type()
    return arg


def pytest_generate_tests(metafunc: Metafunc):
    if 'futures_interface' in metafunc.fixturenames:
        interfaces = [ex.interface for ex in FUTURES_EXCHANGES]
        if 'symbol' in metafunc.fixturenames:
            vals = [(interface, symbol) for interface in interfaces
                    for symbol in SYMBOLS[interface.get_exchange_type()]]
            metafunc.parametrize('futures_interface,symbol', vals, ids=gen_id)
        else:
            metafunc.parametrize('futures_interface', interfaces, ids=gen_id)


def pytest_addoption(parser):
    parser.addoption("--run-orders",
                     action="store_true",
                     default=False,
                     help="run order tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "order: mark as order test")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-orders"):
        # --run-orders given in cli: do not skip order tests
        return
    skip_order = pytest.mark.skip(reason="need --run-orders option to run")
    for item in items:
        if "order" in item.keywords:
            item.add_marker(skip_order)


order_guard = pytest.mark.order


def homogenity_testing(func=None, check_values: bool = False):
    # allow using without arguments
    # this trick brought to you by Python Cookbook
    if func is None:
        return functools.partial(homogenity_testing, values=check_values)

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
    ), f'comparing to {other_name}: types do not match. {this=} {other=}'
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


def wait_till_filled(interface: FuturesExchangeInterface, order: FuturesOrder):
    retries = 0
    res = interface.get_order(order.symbol, order.id)
    while res.status != OrderStatus.FILLED:
        if retries > 2:
            pytest.fail(f"order was not filled in time. status: {res.status}")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(res.symbol, order.id)
    return res


def place_order(interface: FuturesExchangeInterface, symbol: str, side: Side, funds: int = 11, reduce_only: bool = False):
    """
    Helper function to place a market order
    Args:
        interface: the interface to order on
        symbol: the symbol to sell

    Returns: the order object from the interface
    """
    if interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail("the current ftx api key doesn't support trading")
    product = interface.get_products(symbol)
    price = interface.get_price(symbol)
    order_size = utils.trunc(funds / price, product.size_precision)

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

    res = wait_till_filled(interface, order)
    assert res.status == OrderStatus.FILLED

    if reduce_only:
        # 1% tolerance
        assert res.price <= price * 1.01
        assert res.size <= order_size * 1.01

        # set size equal so we can compare
        order.size = res.size
    else:
        assert res.price == approx(price, rel=0.01)
        assert res.size == approx(order_size)

    # set price, status equal so we can compare
    order.price = res.price
    order.status = res.status
    assert order == res

    return order


def sell(interface: FuturesExchangeInterface, symbol: str, funds: int = 11, reduce_only: bool = False):
    return place_order(interface, symbol, Side.SELL, funds, reduce_only)


def buy(interface: FuturesExchangeInterface, symbol: str, funds: int = 11, reduce_only: bool = False):
    return place_order(interface, symbol, Side.BUY, funds, reduce_only)


def close_position(interface: FuturesExchangeInterface, symbol: str):
    """
    Exit position
    Args:
        interface: the interface to sell on
        symbol: the symbol to sell
    """
    if interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail("the current ftx api key doesn't support trading")
    position = interface.get_positions(symbol).size
    if position < 0:
        interface.market_order(symbol,
                               Side.BUY,
                               -position * 2,
                               reduce_only=True)
    elif position > 0:
        interface.market_order(symbol,
                               Side.SELL,
                               position * 2,
                               reduce_only=True)
    assert interface.get_positions(symbol).size == 0


@contextmanager
def cancelling_order(interface: FuturesExchangeInterface, symbol: str):
    """
    Context manager for placing and cancelling a limit order from within a test.
    Useful for testing paths that require active orders.
    Args:
        interface: The interface to place an order on
        symbol: The symbol to buy

    Returns: The order object as returned from the interface
    """
    if interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail("the current ftx api key doesn't support trading")

    product = interface.get_products(symbol)
    price = interface.get_price(symbol)

    # place our limit order
    order_size = utils.trunc(100 / price, product.size_precision)  # $1 order
    limit_price = utils.trunc(price * 0.95, product.price_precision)
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

    yield order

    res = interface.cancel_order(symbol, order.id)
    assert res.status == OrderStatus.CANCELED

    assert order != res
    res.status = OrderStatus.OPEN
    assert order == res
