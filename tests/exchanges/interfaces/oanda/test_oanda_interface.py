import datetime
import time
from datetime import datetime as dt
from pathlib import Path

import dateparser
import pytest
import pytz

from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI
from blankly.exchanges.interfaces.oanda.oanda_auth import OandaAuth
from blankly.exchanges.interfaces.oanda.oanda_interface import OandaInterface
from blankly.exchanges.interfaces.direct_calls_factory import DirectCallsFactory
from tests.helpers.comparisons import validate_response


@pytest.fixture
def oanda_interface():
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    auth_obj = OandaAuth(str(keys_file_path), "oanda test portfolio")
    _, oanda_interface = DirectCallsFactory.create("oanda", auth_obj, str(settings_file_path))
    return oanda_interface


def test_get_exchange(oanda_interface: OandaInterface) -> None:
    assert oanda_interface.get_exchange_type() == 'oanda'


def test_get_price(oanda_interface: OandaInterface) -> None:
    assert isinstance(oanda_interface.get_price("EUR_USD"), float)


def test_get_cash(oanda_interface: OandaInterface) -> None:
    assert isinstance(oanda_interface.cash, float)


def test_marketorder_comprehensive(oanda_interface: OandaInterface) -> None:
    # query for the unique ID of EUR_USD
    products = oanda_interface.get_products()

    found_EUR_USD = False
    for product in products:
        if product['symbol'] == 'EUR_USD':
            found_EUR_USD = True

    assert found_EUR_USD

    EUR_USD = 'EUR_USD'
    market_buy_order = oanda_interface.market_order(EUR_USD, 'buy', 200)

    num_retries = 0
    order_submitted = False
    # wait until order is filled
    resp = None
    while not resp:
        try:
            resp = oanda_interface.get_order(EUR_USD, market_buy_order.get_id())
        except:
            time.sleep(1)
            num_retries += 1
            if num_retries > 10:
                raise TimeoutError("Too many retries, cannot get order status")

    # verify resp is correct
    validate_response(oanda_interface.needed['market_order'], resp)

    market_sell_order = oanda_interface.market_order(EUR_USD, 'sell', 200)
    resp = None
    while not resp:
        try:
            resp = oanda_interface.get_order(EUR_USD, market_buy_order.get_id())
        except:
            time.sleep(1)
            num_retries += 1
            if num_retries > 10:
                raise TimeoutError("Too many retries, cannot get order status")

    # verify resp is correct
    validate_response(oanda_interface.needed['market_order'], resp)


def test_get_products(oanda_interface: OandaInterface) -> None:
    products = oanda_interface.get_products()
    for product in products:
        validate_response(oanda_interface.needed['get_products'], product)


def test_get_account(oanda_interface: OandaInterface) -> None:
    account = oanda_interface.get_account()
    USD_found = False
    for key, val in account.items():
        validate_response(oanda_interface.needed['get_account'], val)
        if key == "USD":
            USD_found = True

    assert USD_found

    account = oanda_interface.get_account('USD')
    assert 'available' in account
    assert 'hold' in account
    assert isinstance(account['available'], float)
    assert isinstance(account['hold'], float)


def test_limitorder_comprehensive(oanda_interface: OandaInterface) -> None:
    pass


def test_get_filters(oanda_interface: OandaInterface) -> None:
    pass


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
