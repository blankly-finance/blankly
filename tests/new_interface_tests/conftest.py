import functools
from datetime import time
import os
from collections import OrderedDict

import pytest
from _pytest.python import Metafunc

from blankly.enums import OrderStatus
from blankly.exchanges.interfaces.binance_futures.binance_futures import BinanceFutures
from blankly.exchanges.interfaces.ftx_futures.ftx_futures import FTXFutures
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder

FUTURES_EXCHANGES = [
    BinanceFutures(keys_path="./tests/config/keys.json",
                   preferences_path="./tests/config/settings.json",
                   portfolio_name="Futures Test Key"),
    FTXFutures(keys_path="./tests/config/keys.json",
               preferences_path="./tests/config/settings.json",
               portfolio_name="Dotcom Test Account"),
]
SYMBOLS = {
    'ftx_futures': ['SOL-USD', 'BTC-USD'],
    'binance_futures': ['BCH-USDT', 'BTC-USDT']
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
        __tracebackhide__ = True
        test_name = os.environ.get('PYTEST_CURRENT_TEST')
        test_name = test_name[test_name.find('[') + 1:test_name.find(']')]
        result = func(*args, **kwargs)
        compare_results(results, result, check_values)
        results[test_name] = result
        return result

    return wrapper


def compare_results(previous_outputs: dict, result, check_values: bool):
    __tracebackhide__ = True
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
        ), f'comparing to {other_name}: dict keys do not match. '\
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
            raise TimeoutError(f"order was not filled. status: {res.status}")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(res.symbol, order.id)
    return res
