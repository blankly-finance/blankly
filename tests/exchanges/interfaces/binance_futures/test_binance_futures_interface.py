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
import time
import unittest
from pathlib import Path

import pytest

import blankly
from blankly import BinanceFutures
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
    assert 0 <= res.BTC.available

def test_order(interface: BinanceFuturesInterface) -> None:
    symbol = 'BTC-USDT'
    sell_order = interface.market_order(symbol, 'sell', .01)

    retries = 0
    res = interface.get_order(symbol, sell_order.get_id())
    while res.status != "FILLED":
        if retries > 2:
            raise TimeoutError("order was not filled")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(symbol, sell_order.get_id())

    assert res.side == 'SELL'
    assert res.type == 'MARKET'

    buy_order = interface.market_order(symbol, 'buy', .01)

    retries = 0
    res = interface.get_order(symbol, buy_order.get_id())
    while res.status != "FILLED":
        if retries > 2:
            raise TimeoutError("order was not filled")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(buy_order.get_id())

    assert res.side == 'BUY'
    assert res.type == 'MARKET'


def test_get_price(interface: BinanceFuturesInterface):
    # test bitcoin price is reasonable
    assert 10 < interface.get_price('BTC-USDT') < 100000


def test_cancel_order(interface: BinanceFuturesInterface):
    symbol = 'BTC-USDT'
    price = int(interface.get_price(symbol) * 0.8)
    buy_order = interface.limit_order(symbol, 'buy', price, .01)

    assert buy_order.get_status() == 'NEW'

    retries = 0
    res = interface.cancel_order(symbol, buy_order.get_id())
    while res.status != "CANCELED":
        if retries > 4:
            raise TimeoutError("order was not cancelled")
        time.sleep(1 << retries)
        retries += 1
        res = interface.get_order(symbol, buy_order.get_id())
