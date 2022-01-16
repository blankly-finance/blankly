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

from blankly.exchanges.interfaces.binance.binance_interface import BinanceInterface
from blankly.utils.utils import AttributeDict


class BinanceInterface_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Binance = blankly.Binance(portfolio_name="Spot Test Key",
                                      keys_path="./tests/config/keys.json",
                                      settings_path="./tests/config/settings.json")
        cls.Binance_Interface = cls.Binance.get_interface()

    def test_get_exchange_type(self):
        binance = self.Binance_Interface.get_exchange_type()
        self.assertEqual(binance, "binance")


@pytest.fixture
def binance_interface():
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    binance = blankly.Binance(keys_path=keys_file_path,
                              settings_path=settings_file_path, portfolio_name='Spot Test Key')

    return binance.interface


def test_get_exchange(binance_interface: BinanceInterface) -> None:
    assert binance_interface.get_exchange_type() == 'binance'


def test_get_account(binance_interface: BinanceInterface) -> None:
    resp = binance_interface.get_account()
    assert type(resp) is AttributeDict

    found_btc = False
    for asset in resp.keys():
        if asset == "BTC":
            resp['BTC']['available'] += 1
            resp['BTC']['hold'] += 1

            found_btc = True

    assert found_btc


def test_get_buy_sell_order(binance_interface: BinanceInterface) -> None:
    # query for the unique ID of BTC-USD
    products = binance_interface.get_products()
    btc_usd_id = None

    for i in products:
        if i['symbol'] == 'BTC-USDT':
            btc_usd_id = i['symbol']
            break
    print(btc_usd_id)
    assert btc_usd_id

    market_buy_order = binance_interface.market_order(btc_usd_id, 'buy', .01)

    time.sleep(1.5)

    num_retries = 0
    # wait until order is filled
    while binance_interface.get_order(btc_usd_id, market_buy_order.get_id())['status'] != "filled":
        time.sleep(1)
        num_retries += 1
        if num_retries > 10:
            raise TimeoutError("Too many retries, cannot get order status")

    resp = binance_interface.get_order(btc_usd_id, market_buy_order.get_id())
    assert type(resp) is dict
    assert resp["side"] == "buy"
    assert resp["type"] == "market"

    market_sell_order = binance_interface.market_order(btc_usd_id, 'sell', .01)
    # this test has been flaky, so lets add a sleep for engine to process order
    time.sleep(1)
    # wait until order is filled
    while binance_interface.get_order(btc_usd_id, market_sell_order.get_id())['status'] != "filled":
        time.sleep(1)
        num_retries += 1
        if num_retries > 10:
            raise TimeoutError("Too many retries, cannot get order status")

    resp = binance_interface.get_order(btc_usd_id, market_sell_order.get_id())
    assert type(resp) is dict
    assert resp["side"] == "sell"
    assert resp["type"] == "market"


def test_get_price(binance_interface: BinanceInterface) -> None:
    # todo: just call a couple of popular coins and see if they all return floats
    btcusd = 'BTC-USDT'
    resp = binance_interface.get_price(btcusd)
    assert type(resp) is float