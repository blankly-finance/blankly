"""
    Oanda interface custom unit tests.
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
from pathlib import Path

import pytest

import blankly
from blankly.exchanges.interfaces.oanda.oanda_interface import OandaInterface
from tests.helpers.comparisons import validate_response
from tests.testing_utils import forex_market_open


@pytest.fixture
def oanda_interface():
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    oanda = blankly.Oanda(keys_path=keys_file_path,
                          settings_path=settings_file_path,
                          portfolio_name='oanda test portfolio')

    # auth_obj = OandaAuth(str(keys_file_path), "oanda test portfolio")
    # _, oanda_interface = DirectCallsFactory.create("oanda", auth_obj, str(settings_file_path))
    return oanda.interface


def test_get_exchange(oanda_interface: OandaInterface) -> None:
    assert oanda_interface.get_exchange_type() == 'oanda'


def test_get_price(oanda_interface: OandaInterface) -> None:
    assert isinstance(oanda_interface.get_price("EUR-USD"), float)
    assert isinstance(oanda_interface.get_price("ZAR-JPY"), float)


def test_get_cash(oanda_interface: OandaInterface) -> None:
    assert isinstance(oanda_interface.cash, float)


def test_marketorder_comprehensive(oanda_interface: OandaInterface) -> None:
    # query for the unique ID of EUR_USD
    if not forex_market_open():
        return

    products = oanda_interface.get_products()

    found_eur_usd = False
    for product in products:
        if product['symbol'] == 'EUR-USD':
            found_eur_usd = True

    assert found_eur_usd

    eur_usd = 'EUR-USD'
    market_buy_order = oanda_interface.market_order(eur_usd, 'buy', 200)

    time.sleep(2)
    resp = oanda_interface.get_order(eur_usd, market_buy_order.get_id())

    # verify resp is correct
    validate_response(oanda_interface.needed['market_order'], resp)

    # Todo: validate market sell order object can query its info correctly
    oanda_interface.market_order(eur_usd, 'sell', 200)

    time.sleep(2)
    resp = oanda_interface.get_order(eur_usd, market_buy_order.get_id())

    # verify resp is correct
    validate_response(oanda_interface.needed['market_order'], resp)


def test_get_products(oanda_interface: OandaInterface) -> None:
    products = oanda_interface.get_products()
    for product in products:
        validate_response(oanda_interface.needed['get_products'], product)


def test_get_account(oanda_interface: OandaInterface) -> None:
    account = oanda_interface.get_account()
    usd_found = False
    for key, val in account.items():
        validate_response(oanda_interface.needed['get_account'], val)
        if key == "USD":
            usd_found = True

    assert usd_found

    account = oanda_interface.get_account('USD')
    assert 'available' in account
    assert 'hold' in account
    assert isinstance(account['available'], float)
    assert isinstance(account['hold'], float)


def test_limitorder_comprehensive(oanda_interface: OandaInterface) -> None:
    eur_usd = 'EUR-USD'
    limit_buy_order = oanda_interface.limit_order(eur_usd, 'buy', 1, 5)

    time.sleep(1)
    resp = oanda_interface.get_order(eur_usd, limit_buy_order.get_id())

    validate_response(oanda_interface.needed['limit_order'], resp)

    # now cancel the order
    resp = oanda_interface.cancel_order(eur_usd, limit_buy_order.get_id())
    validate_response(oanda_interface.needed['cancel_order'], resp)


def test_get_order(oanda_interface: OandaInterface) -> None:
    locally_created_orders = []
    for i in range(5):
        locally_created_orders.append(oanda_interface.limit_order("EUR-USD", 'buy', 1, 5))
        time.sleep(0.1)

    orders = oanda_interface.get_open_orders()
    for order in orders:
        needed = oanda_interface.choose_order_specificity(order['type'])
        validate_response(needed, order)

    orders = oanda_interface.get_open_orders("EUR-USD")
    for order in orders:
        needed = oanda_interface.choose_order_specificity(order['type'])
        validate_response(needed, order)

    for order in locally_created_orders:
        resp = oanda_interface.cancel_order("EUR-USD", order.get_id())
        validate_response(oanda_interface.needed['cancel_order'], resp)


def test_get_filters(oanda_interface: OandaInterface) -> None:
    products = oanda_interface.get_products()
    for product in products:
        resp = oanda_interface.get_order_filter(product['symbol'])
        validate_response(oanda_interface.needed['get_order_filter'], resp)


def test_get_product_history(oanda_interface: OandaInterface) -> None:
    pass


def test_history(oanda_interface: OandaInterface) -> None:
    pass

#
# def test_get_all_open_orders(oanda_interface: OandaInterface) -> None:
#     start = dateparser.parse("2021-02-04 9:30AM EST").timestamp()
#     end = dateparser.parse("2021-02-04 9:35AM EST").timestamp()
#
#     # bars = oanda_interface.history("EUR_USD", to=5, resolution=60)
#     # bars = oanda_interface.history("EUR_USD", to=5, resolution=60, end_date=end)
#     bars = oanda_interface.history("EUR_USD", to=5, resolution=60*3, end_date=end)
#     assert False
#
