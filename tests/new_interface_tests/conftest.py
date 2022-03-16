import functools
import sys
from datetime import time

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
    'ftx_futures': ['SOL-USD', 'BTC-USD', 'ETH-USD'],
    'binance_futures': ['LTC-USDT', 'BTC-USDT', 'ETH-USDT']
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
    parser.addoption(
        "--run-orders", action="store_true", default=False, help="run order tests"
    )


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

def homogenity_testing(func=None, values: bool = False):
    # allow using without arguments
    # this trick brought to you by Python Cookbook
    if func is None:
        return functools.partial(homogenity_testing, values=values)

    previous_outputs = []

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        output = func(*args, **kwargs)
        compare_to_previous(previous_outputs, output, values)
        previous_outputs.append(output)
        last_output = output
        return output

    return wrapper


# TODO https://docs.pytest.org/en/6.2.x/example/simple.html#writing-well-integrated-assertion-helpers
def compare_to_previous(previous_outputs: list, current, values: bool):
    for prev in previous_outputs:
        compare_values(prev, current, values)


def compare_values(a, b, values: bool):
    assert type(a) == type(b)
    if isinstance(a, list):
        if a and b:
            for val in a[1:] + b:
                compare_values(a[0], val, values)
    if isinstance(a, dict):
        a.pop('exchange_specific', None)
        b.pop('exchange_specific', None)
        assert a.keys() == b.keys()
        for key in a:
            compare_values(a[key], b[key], values)
    elif values:
        assert a == b


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
