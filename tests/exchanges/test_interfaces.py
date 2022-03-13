import random
import time
from operator import itemgetter

import pytest
from _pytest.python import Metafunc

from blankly import BinanceFutures, Side, OrderStatus, OrderType
from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.interfaces.ftx_futures.ftx_futures import FTXFutures
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from datetime import datetime

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
    'ftx_futures': ['BTC-PERP', 'ETH-PERP', 'BTC-0626', 'BTC-MOVE-1005'],
    'binance_futures': ['BTC-USDT', 'ETH-USDT']
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
    res = futures_interface.get_account()
    assert 0 <= res.USDT.available


def test_account_leverage(futures_interface: FuturesExchangeInterface):
    if futures_interface.get_exchange_type() == 'binance_futures':
        pytest.xfail('Binance Futures does not support setting account leverage')
    futures_interface.set_leverage(3)
    assert futures_interface.get_leverage() == 3


def test_symbol_leverage(futures_interface: FuturesExchangeInterface,
                         symbol: str):
    if futures_interface.get_exchange_type() == 'ftx_futures':
        pytest.xfail('FTX Futures does not support setting account leverage')
    futures_interface.set_leverage(3, symbol)
    assert futures_interface.get_leverage(symbol) == 3


def test_order(futures_interface: FuturesExchangeInterface,
               symbol: str) -> None:
    sell_order = futures_interface.market_order(symbol, Side.SELL, .01)

    retries = 0
    res = futures_interface.get_order(symbol, sell_order.id)
    while res.status != OrderStatus.FILLED:
        if retries > 2:
            raise TimeoutError(f"order was not filled. status: {res.status}")
        time.sleep(1 << retries)
        retries += 1
        res = futures_interface.get_order(symbol, sell_order.id)

    assert res.side == Side.SELL
    assert res.type == OrderType.MARKET

    buy_order = futures_interface.market_order(symbol, Side.BUY, .01)

    retries = 0
    res = futures_interface.get_order(symbol, buy_order.id)
    while res.status != OrderStatus.FILLED:
        if retries > 2:
            raise TimeoutError("order was not filled")
        time.sleep(1 << retries)
        retries += 1
        res = futures_interface.get_order(buy_order.id)

    assert res.side == Side.BUY
    assert res.type == OrderType.MARKET


def test_cancel_order(futures_interface: FuturesExchangeInterface,
                      symbol: str):
    price = futures_interface.get_price(symbol)
    buy_order = futures_interface.limit_order(symbol, Side.BUY,
                                              utils.trunc(price * 0.95, 1),
                                              utils.trunc(100 / price, 3))

    assert buy_order.status == OrderStatus.NEW

    retries = 0
    res = futures_interface.cancel_order(symbol, buy_order.id)
    while res.status != OrderStatus.CANCELED:
        if retries > 2:
            raise TimeoutError("order was not cancelled")
        time.sleep(1 << retries)
        retries += 1
        res = futures_interface.get_order(symbol, buy_order.id)


def test_funding_rate_history(futures_interface: FuturesExchangeInterface,
                              symbol: str):
    day = 60 * 60 * 24
    now = int(datetime.now().timestamp())
    start = now - day * 365
    end = now - day * 7
    history = futures_interface.get_funding_rate_history(symbol=symbol,
                                                         epoch_start=start,
                                                         epoch_stop=end)

    # test start and end times
    assert start <= history[0]['time'] < start + day
    assert end - day < history[-1]['time'] <= end

    # test ascending order
    assert sorted(history, key=itemgetter('time')) == history
