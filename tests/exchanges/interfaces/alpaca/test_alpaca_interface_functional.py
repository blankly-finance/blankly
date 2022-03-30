"""
    Custom alpaca unit tests
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
from datetime import datetime as dt
from pathlib import Path

import alpaca_trade_api
import dateparser
import dateparser as dp
import pytest
import pytz

import blankly
from blankly.exchanges.interfaces.alpaca.alpaca_interface import AlpacaInterface

timeZ_Ny = pytz.timezone('America/New_York')
MARKET_OPEN = datetime.time(hour=9, minute=0, second=0, tzinfo=timeZ_Ny)
MARKET_CLOSE = datetime.time(hour=17, minute=0, second=0, tzinfo=timeZ_Ny)


@pytest.fixture
def alpaca_interface():
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    alpaca = blankly.Alpaca(keys_path=keys_file_path,
                            settings_path=settings_file_path,
                            portfolio_name="alpaca test portfolio")

    # auth_obj = AlpacaAuth(str(keys_file_path), "alpaca test portfolio")
    # _, alpaca_interface = DirectCallsFactory.create("alpaca", auth_obj, str(settings_file_path))
    return alpaca.interface


def test_get_exchange(alpaca_interface: AlpacaInterface) -> None:
    assert alpaca_interface.get_exchange_type() == 'alpaca'


# TODO: uncomment and fix this when we get the function to work
# def test_get_products(alpaca_interface: AlpacaInterface) -> None:
#     return_val = alpaca_interface.get_products()
#
#     expected_answer = {
#         "symbol": "AAPL-USD",
#         "base_asset": "AAPL",
#         "quote_asset": "USD",
#         "base_min_size": -1,
#         "base_max_size": -1,
#         "base_increment": -1,
#     }
#     for k, v in expected_answer.items():
#         assert return_val[0][k] == v
#
#     assert "exchange_specific" in return_val[0]

def test_get_buy_sell(alpaca_interface: AlpacaInterface) -> None:
    if not alpaca_interface.get_calls().get_clock()['is_open']:
        return

    known_apple_info = {
        "id": "904837e3-3b76-47ec-b432-046db621571b",
        "class": "us_equity",
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "status": "active",
        "tradable": True,
        "marginable": True,
        "shortable": True,
        "easy_to_borrow": True,
        "fractionable": True
    }

    # query for the unique ID of AAPL
    products = alpaca_interface.get_products()
    apple_id = None

    for product in products:
        if product['base_asset'] == 'AAPL':
            apple_id = product['exchange_specific']['id']

    assert apple_id

    market_order = alpaca_interface.market_order(apple_id, 'buy', 1)

    num_retries = 0
    # wait until order is filled
    while alpaca_interface.get_order('AAPL', market_order.get_id())['size'] is None:
        time.sleep(1)
        num_retries += 1
        if num_retries > 10:
            raise TimeoutError("Too many retries, cannot get order status")

    resp = alpaca_interface.get_order('AAPL', market_order.get_id())

    # get_position(symbol)

    # get_asset(symbol)

    # place sell order


def test_get_product_history(alpaca_interface: AlpacaInterface) -> None:
    start = dt.strptime("2021-02-04", "%Y-%m-%d").timestamp()
    end = dt.strptime("2021-02-05", "%Y-%m-%d").timestamp()

    return_df = alpaca_interface.get_product_history("AAPL", start, end, 60)
    return_df_2 = alpaca_interface.get_product_history("AAPL", start, end, 120)
    assert len(return_df) > 0
    assert len(return_df) >= len(return_df_2)


def test_get_product_history_est_timezone(alpaca_interface: AlpacaInterface) -> None:
    start = dateparser.parse("2021-02-04 9:30AM EST").timestamp()
    end = dateparser.parse("2021-02-04 9:35AM EST").timestamp()

    return_df = alpaca_interface.get_product_history("AAPL", start, end, 60)
    desired_timestamp = dp.parse("2021-02-04 14:30:00+00:00").timestamp()
    assert return_df.iloc[0]['time'] == desired_timestamp
    assert (len(return_df) == 6)


def test_get_product_history_custom(alpaca_interface: AlpacaInterface) -> None:
    assert isinstance(alpaca_interface.calls, alpaca_trade_api.REST)
    end = dateparser.parse("2021-02-04 9:35AM EST")

    return_df = alpaca_interface.history("AAPL", to=10, resolution='1h', end_date=end)
    assert (len(return_df) == 10)


def test_get_account(alpaca_interface: AlpacaInterface) -> None:
    products = alpaca_interface.get_account()
    for _, val in products.items():
        assert 'available' in val
        assert 'hold' in val

    assert "USD" in products


def test_get_price(alpaca_interface: AlpacaInterface) -> None:
    price = alpaca_interface.get_price("AAPL")
    assert isinstance(price, float)

def test_get_open_orders(alpaca_interface: AlpacaInterface) -> None:
    orders = alpaca_interface.get_open_orders()
    print(orders)
