"""
    Custom alpaca interface unit tests
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

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import blankly


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

    def list_orders(self, *args, **kwargs):
        mock_orders_response = [{
            "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
            "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
            "created_at": "2021-03-16T18:38:01.942282Z",
            "updated_at": "2021-03-16T18:38:01.942282Z",
            "submitted_at": "2021-03-16T18:38:01.937734Z",
            "filled_at": None,
            "expired_at": None,
            "canceled_at": None,
            "failed_at": None,
            "replaced_at": None,
            "replaced_by": None,
            "replaces": None,
            "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
            "symbol": "AAPL",
            "asset_class": "us_equity",
            "notional": None,
            "qty": 1,
            "filled_qty": "0",
            "filled_avg_price": None,
            "order_class": "",
            "order_type": "market",
            "type": "market",
            "side": "sell",
            "time_in_force": "day",
            "limit_price": None,
            "stop_price": None,
            "status": "accepted",
            "extended_hours": False,
            "legs": None,
            "trail_percent": None,
            "trail_price": None,
            "hwm": None
        }]

        return mock_orders_response

    def get_snapshots(self, symbols):
        mock_snapshots = [{
            "symbol": "AAPL",
            "latestTrade": {
                "t": "2021-05-11T20:00:00.435997104Z",
                "x": "Q",
                "p": 125.91,
                "s": 5589631,
                "c": [
                    "@",
                    "M"
                ],
                "i": 179430,
                "z": "C"
            },
            "latestQuote": {
                "t": "2021-05-11T22:05:02.307304704Z",
                "ax": "P",
                "ap": 125.68,
                "as": 12,
                "bx": "P",
                "bp": 125.6,
                "bs": 4,
                "c": [
                    "R"
                ]
            },
            "minuteBar": {
                "t": "2021-05-11T22:02:00Z",
                "o": 125.66,
                "h": 125.66,
                "l": 125.66,
                "c": 125.66,
                "v": 396
            },
            "dailyBar": {
                "t": "2021-05-11T04:00:00Z",
                "o": 123.5,
                "h": 126.27,
                "l": 122.77,
                "c": 125.91,
                "v": 125863164
            },
            "prevDailyBar": {
                "t": "2021-05-10T04:00:00Z",
                "o": 129.41,
                "h": 129.54,
                "l": 126.81,
                "c": 126.85,
                "v": 79569305
            }
        }]

        return mock_snapshots

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
def alpaca_mock_interface(mocker: MockerFixture):
    keys_file_path = Path("tests/config/keys.json").resolve().__str__()
    settings_file_path = Path("tests/config/settings.json").resolve().__str__()

    mocker.patch("alpaca_trade_api.REST", new=mock_alpaca_direct_calls)
    alpaca = blankly.Alpaca(keys_path=keys_file_path,
                            settings_path=settings_file_path,
                            portfolio_name="alpaca test portfolio")
    # auth_obj = AlpacaAuth(keys_file_path, "alpaca test portfolio")
    # _, alpaca_interface = DirectCallsFactory.create("alpaca", auth_obj, settings_file_path)

    return alpaca.interface


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


# TODO: make this test better
def test_get_account(alpaca_mock_interface) -> None:
    return_val = alpaca_mock_interface.get_account()

    expected_answer = {
        "AAPL": {
            "available": 4,
            "hold": 1,
        }
    }

    assert 'AAPL' in return_val
    assert return_val['AAPL']['available'] == 4
    assert return_val['AAPL']['hold'] == 1


def test_get_cash(alpaca_mock_interface) -> None:
    expected_answer = 262113.632
    return_val = alpaca_mock_interface.cash
    assert return_val == expected_answer


def test_get_fees(alpaca_mock_interface) -> None:
    fee_response = alpaca_mock_interface.get_fees()
    assert fee_response['maker_fee_rate'] == 0
    assert fee_response['taker_fee_rate'] == 0
