import random
import time
from operator import itemgetter

import pytest
from _pytest.python import Metafunc

from blankly.enums import Side, OrderStatus, OrderType, ContractType
from blankly.exchanges.interfaces.binance_futures.binance_futures import BinanceFutures
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.ftx_futures.ftx_futures import FTXFutures
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from datetime import datetime

from blankly.exchanges.orders.futures.futures_order import FuturesOrder
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
    'ftx_futures': ['LUNA-PERP', 'SOL-PERP', 'SOL-0325'],
    'binance_futures': ['LTC-USDT', 'BCH-USDT']
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


def test_account(futures_interface: FuturesExchangeInterface):
    assert 0 <= futures_interface.get_account('USDT').available


def test_account_leverage(futures_interface: FuturesExchangeInterface):
    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail(
            'Binance Futures does not support setting account leverage')
    futures_interface.set_leverage(3)
    assert futures_interface.get_leverage() == 3


def test_symbol_leverage(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support setting account leverage')
    futures_interface.set_leverage(3, symbol)
    assert futures_interface.get_leverage(symbol) == 3


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


def test_order(futures_interface: FuturesExchangeInterface,
               symbol: str) -> None:
    init_position = futures_interface.get_positions(symbol).size
    product = futures_interface.get_products(symbol)
    price = futures_interface.get_price(symbol)
    size = utils.trunc(1 / price, product.price_precision)

    sell_order = futures_interface.market_order(symbol, Side.SELL, size)
    res = wait_till_filled(futures_interface, sell_order)

    assert res.side == Side.SELL
    assert res.type == OrderType.MARKET
    assert futures_interface.get_positions(symbol).size == init_position - size

    buy_order = futures_interface.market_order(symbol,
                                               Side.BUY,
                                               size,
                                               reduce_only=True)
    res = wait_till_filled(futures_interface, buy_order)

    assert res.side == Side.BUY
    assert res.type == OrderType.MARKET
    assert futures_interface.get_positions(symbol).size == init_position


def test_cancel_order(futures_interface: FuturesExchangeInterface,
                      symbol: str):
    init_position = futures_interface.get_positions(symbol).size
    product = futures_interface.get_products(symbol)

    price = futures_interface.get_price(symbol)
    size = utils.trunc(1 / price, product.size_precision)
    buy_order = futures_interface.limit_order(symbol, Side.BUY,
                                              utils.trunc(price * 0.95, product.price_precision),
                                              size)

    assert buy_order.status == OrderStatus.OPEN

    res = futures_interface.cancel_order(symbol, buy_order.id)
    assert res.status == OrderStatus.CANCELED
    assert init_position == futures_interface.get_positions(symbol).size


def test_funding_rate_history(futures_interface: FuturesExchangeInterface,
                              symbol: str):
    day = 60 * 60 * 24
    now = int(datetime.now().timestamp())
    start = now - day * 365
    end = now - day * 7
    history = futures_interface.get_funding_rate_history(symbol=symbol,
                                                         epoch_start=start,
                                                         epoch_stop=end)

    # non-perp contracts don't have funding rates
    if futures_interface.get_products()[symbol].contract_type != ContractType.PERPETUAL:
        assert len(history) == 0
        return

    # test start and end times
    assert start <= history[0]['time'] < start + day
    assert end - day < history[-1]['time'] <= end

    # test ascending order
    assert sorted(history, key=itemgetter('time')) == history


def test_price(futures_interface: FuturesExchangeInterface, symbol: str):
    price = futures_interface.get_price(symbol)
    assert 0 < price
