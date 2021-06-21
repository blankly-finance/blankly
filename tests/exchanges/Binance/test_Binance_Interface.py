"""
    Unit tests for Binance.
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
import pytest

import Blankly
import unittest

from Blankly.auth.Binance.auth import BinanceAuth
from Blankly.auth.direct_calls_factory import InterfaceFactory
from Blankly.exchanges.Binance.Binance_Interface import BinanceInterface
from Blankly.utils.utils import compare_dictionaries
from pathlib import Path
import time

class BinanceInterface_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Binance = Blankly.Binance(portfolio_name="Spot Test Key",
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

    auth_obj = BinanceAuth(str(keys_file_path), "Spot Test Key")
    _, binance_interface = InterfaceFactory.create("binance", auth_obj, str(settings_file_path))
    return binance_interface


def test_get_exchange(binance_interface: BinanceInterface) -> None:
    assert binance_interface.get_exchange_type() == 'binance'

def test_get_account(binance_interface: BinanceInterface) -> None:
    resp = binance_interface.get_account()
    assert type(resp) is list

    found_btc = False
    for asset in resp:
        if(asset['currency'] == "BTC"):
            found_btc = True

    assert found_btc

def test_get_buy_sell_order(binance_interface: BinanceInterface) -> None:
    # query for the unique ID of BTC-USD
    products = binance_interface.get_products()
    btc_usd_id = None

    for product in products:
        if product['base_currency'] == 'BTC':
            btc_usd_id = product['currency_id']
    print(btc_usd_id)
    assert btc_usd_id

    market_buy_order = binance_interface.market_order(btc_usd_id, 'buy', 200)

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

    market_sell_order = binance_interface.market_order(btc_usd_id, 'sell', 200)

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