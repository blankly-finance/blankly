"""
    Unit tests for binance.
    Copyright (C) 2021  Emerson Dove

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
import datetime
import time
from operator import itemgetter

import pytest

from blankly import BinanceFutures, Side, OrderStatus, OrderType
from blankly.exchanges.interfaces.binance_futures.binance_futures_interface import BinanceFuturesInterface


@pytest.fixture
def exchange() -> BinanceFutures:
    return BinanceFutures(keys_path="./tests/config/keys.json",
                          preferences_path="./tests/config/settings.json",
                          portfolio_name="Futures Test Key")


@pytest.fixture
def interface(exchange: BinanceFutures) -> BinanceFuturesInterface:
    exchange.interface.init_exchange()
    return exchange.interface


def test_exchange_type(exchange: BinanceFutures):
    assert exchange.exchange_type == 'binance_futures'


def test_account(interface: BinanceFuturesInterface):
    res = interface.get_account()
    assert 0 <= res.USDT.available


def test_order(interface: BinanceFuturesInterface) -> None:
    symbol = 'BTC-USDT'
    sell_order = interface.market_order(symbol, Side.SELL, .01)

    retries = 0
    res = interface.get_order(symbol, sell_order.id)
    while res.status != OrderStatus.FILLED:
        if retries > 2:
            raise TimeoutError(f"order was not filled. status: {res.status}")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(symbol, sell_order.id)

    assert res.side == Side.SELL
    assert res.type == OrderType.MARKET

    buy_order = interface.market_order(symbol, Side.BUY, .01)

    retries = 0
    res = interface.get_order(symbol, buy_order.id)
    while res.status != OrderStatus.FILLED:
        if retries > 2:
            raise TimeoutError("order was not filled")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(buy_order.id)

    assert res.side == Side.BUY
    assert res.type == OrderType.MARKET


def test_get_price(interface: BinanceFuturesInterface):
    # test bitcoin price is reasonable
    assert 10 < interface.get_price('BTC-USDT') < 100000


def test_cancel_order(interface: BinanceFuturesInterface):
    symbol = 'BTC-USDT'
    price = int(interface.get_price(symbol) * 0.8)
    buy_order = interface.limit_order(symbol, Side.BUY, price, .01)

    assert buy_order.status == OrderStatus.OPEN

    retries = 0
    res = interface.cancel_order(symbol, buy_order.id)
    while res.status != OrderStatus.CANCELED:
        if retries > 2:
            raise TimeoutError("order was not cancelled")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(symbol, buy_order.id)


def test_funding_rate_history(interface: BinanceFuturesInterface):
    day = 60 * 60 * 24
    now = int(datetime.datetime.now().timestamp())
    start = now - day * 365
    end = now - day * 7
    history = interface.get_funding_rate_history(symbol='BTC-USDT',
                                                 epoch_start=start,
                                                 epoch_stop=end)

    # test start and end times
    assert start <= history[0]['time'] < start + day
    assert end - day < history[-1]['time'] <= end

    # test ascending order
    assert sorted(history, key=itemgetter('time')) == history
