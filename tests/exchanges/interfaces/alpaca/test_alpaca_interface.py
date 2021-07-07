from Blankly.exchanges.interfaces.alpaca.alpaca_auth import AlpacaAuth
from Blankly.exchanges.interfaces.direct_calls_factory import DirectCallsFactory
import pytest
from pytest_mock import MockerFixture

from tests.helpers.comparisons import is_sub_dict
from pathlib import Path


class mock_alpaca_direct_calls:
    def __init__(self, *args, **kwargs):
        pass

    def get_account(self):
        mock_account_response = {
            "account_blocked": False,
            "account_number": "010203ABCD",
            "buying_power": "262113.632",
            "cash": "1500",
            "created_at": "2019-06-12T22:47:07.99658Z",
            "currency": "USD",
            "daytrade_count": 0,
            "daytrading_buying_power": "262113.632",
            "equity": "103820.56",
            "id": "e6fe16f3-64a4-4921-8928-cadf02f92f98",
            "initial_margin": "63480.38",
            "last_equity": "103529.24",
            "last_maintenance_margin": "38000.832",
            "long_market_value": "126960.76",
            "maintenance_margin": "38088.228",
            "multiplier": "4",
            "pattern_day_trader": False,
            "portfolio_value": "103820.56",
            "regt_buying_power": "80680.36",
            "short_market_value": "0",
            "shorting_enabled": True,
            "sma": "0",
            "status": "ACTIVE",
            "trade_suspended_by_user": False,
            "trading_blocked": False,
            "transfers_blocked": False
        }
        return mock_account_response

    def list_positions(self):
        mock_positions_response = [{
            "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "asset_class": "us_equity",
            "avg_entry_price": "100.0",
            "qty": "5",
            "side": "long",
            "market_value": "600.0",
            "cost_basis": "500.0",
            "unrealized_pl": "100.0",
            "unrealized_plpc": "0.20",
            "unrealized_intraday_pl": "10.0",
            "unrealized_intraday_plpc": "0.0084",
            "current_price": "120.0",
            "lastday_price": "119.0",
            "change_today": "0.0084"
        }]
        return mock_positions_response

    def list_assets(self, *args, **kwargs):
        mock_products_response = [{
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
        }]
        return mock_products_response


class mock_alpaca_interface:
    def __init__(self, *args, **kwargs):
        pass

    def get_account(self):
        return "hello"


@pytest.fixture
def alpaca_mock_interface(mocker: MockerFixture) -> None:
    keys_file_path = Path("tests/config/keys.json").resolve()
    settings_file_path = Path("tests/config/settings.json").resolve()

    auth_obj = AlpacaAuth(keys_file_path, "alpaca test portfolio")
    mocker.patch("alpaca_trade_api.REST", new=mock_alpaca_direct_calls)
    _, alpaca_interface = DirectCallsFactory.create("alpaca", auth_obj, settings_file_path)

    return alpaca_interface

# TODO: Need to create a functional testing package
# @pytest.fixture
# def alpaca_interface(mocker: MockerFixture) -> None:
#     keys_file_path = Path("tests/config/keys.json").resolve()
#     settings_file_path = Path("tests/config/settings.json").resolve()
#
#     auth_obj = alpaca_auth(keys_file_path, "alpaca test portfolio")
#     alpaca_interface = DirectCallsFactory.create_interface("alpaca", auth_obj, settings_file_path)
#     return alpaca_interface
#
#
# def test_alpaca_interface_functional(alpaca_interface) -> None:
#
#     assert alpaca_interface.get_exchange_type() == 'alpaca'


def test_get_products(alpaca_mock_interface) -> None:
    return_val = alpaca_mock_interface.get_products()

    expected_answer = {
        "currency_id": "AAPL-USD",
        "base_asset": "AAPL",
        "quote_asset": "USD",
        "base_min_size": -1,
        "base_max_size": -1,
        "base_increment": -1,
    }
    for k, v in expected_answer.items():
        assert return_val[0][k] == v

    assert "exchange_specific" in return_val[0]


def test_get_account(alpaca_mock_interface) -> None:
    return_val = alpaca_mock_interface.get_account()

    expected_answer = {
        "AAPL": {
            "available": 5,
            "hold": 0,
        }
    }
    print(return_val)
    for answer in expected_answer:
        found = False
        for result in return_val:
            if is_sub_dict(expected_answer[answer], return_val[result]):
                found = True

        assert found, "expected return element not found: %r" % answer
    # assert "exchange_specific" in return_val[0]

def test_get_cash(alpaca_mock_interface) -> None:
    expected_answer = 1500
    return_val = alpaca_mock_interface.cash
    assert(return_val == expected_answer)

def test_get_fees(alpaca_mock_interface) -> None:
    fee_response = alpaca_mock_interface.get_fees()
    assert fee_response['maker_fee_rate'] == 0
    assert fee_response['taker_fee_rate'] == 0
