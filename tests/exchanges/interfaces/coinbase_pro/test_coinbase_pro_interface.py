"""
    Unit tests for Coinbase Pro.
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
import unittest
from datetime import datetime as dt
from pathlib import Path

import dateparser
import pytest

import blankly
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_auth import CoinbaseProAuth
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_interface import CoinbaseProInterface
from blankly.exchanges.interfaces.direct_calls_factory import DirectCallsFactory


class CoinbaseInterface2(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Coinbase_Pro = blankly.CoinbasePro(portfolio_name="Sandbox Portfolio",
                                               keys_path='./tests/config/keys.json',
                                               settings_path="./tests/config/settings.json")
        cls.Coinbase_Pro_Interface = cls.Coinbase_Pro.get_interface()

    def test_get_exchange_type(self):
        coinbase_pro = self.Coinbase_Pro_Interface.get_exchange_type()
        self.assertEqual(coinbase_pro, "coinbase_pro")


@pytest.fixture
def coinbase_interface():
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    auth_obj = CoinbaseProAuth(str(keys_file_path), "Sandbox Portfolio")
    _, coinbase_interface = DirectCallsFactory.create("coinbase_pro", auth_obj, str(settings_file_path))
    return coinbase_interface


def test_get_exchange(coinbase_interface: CoinbaseProInterface) -> None:
    assert coinbase_interface.get_exchange_type() == 'coinbase_pro'

    products = coinbase_interface.get_products()
    btc_usd_id = None

    for product in products:
        if product['base_asset'] == 'BTC' and product['quote_asset'] == 'USD':
            btc_usd_id = product['symbol']

    assert btc_usd_id

    # market_buy_order = coinbase_interface.market_order(btc_usd_id, 'buy', 200)


def test_get_price(coinbase_interface: CoinbaseProInterface) -> None:
    responses = []
    responses.append(coinbase_interface.get_price('BTC-USD'))
    responses.append(coinbase_interface.get_price('BTC-EUR'))
    responses.append(coinbase_interface.get_price('BTC-GBP'))
    responses.append(coinbase_interface.get_price('ETH-BTC'))
    for resp in responses:
        assert type(resp) is float


def test_start_with_end_history(coinbase_interface: CoinbaseProInterface) -> None:
    # This initial selection could fail because of the slightly random day that they delete their data
    start_dt = dateparser.parse("2021-08-4")
    start = str(start_dt.replace(day=1).date())
    stop = str(start_dt.date())

    # The dates are offset by one because the time is the open time
    close_stop = str(dt.today().replace(day=start_dt.day - 1).date())

    resp = coinbase_interface.history('BTC-USD', resolution='1h', start_date=start, end_date=stop)

    start_date = dt.fromtimestamp(resp['time'][0]).strftime('%Y-%m-%d')
    end_date = dt.fromtimestamp(resp['time'].iloc[-1]).strftime('%Y-%m-%d')

    assert start_date == start
    assert end_date == close_stop
