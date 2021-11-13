"""
    OANDA root API calls & definitions.
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


import json

from blankly.exchanges.auth.abc_auth import ABCAuth
import requests
from collections import OrderedDict

from blankly.utils.exceptions import APIException


def api_error_handler(func):
    def wrapper(*args, **kwargs):
        resp = func(*args, **kwargs)
        if 'errorMessage' in resp:
            raise APIException(str(resp))
        return resp
    return wrapper


class OandaAPI:
    # documentation here: http://developer.oanda.com/rest-live-v20/account-ep/
    API_URL = 'https://api-fxtrade.oanda.com'
    API_PRACTICE_URL = 'https://api-fxpractice.oanda.com'

    def __init__(self, auth: ABCAuth, sandbox: bool = False):
        self.__api_key = auth.keys['PERSONAL_ACCESS_TOKEN']
        self.default_account = auth.keys['ACCOUNT_ID']

        if not sandbox:
            self.__api_url = self.API_URL
        else:
            self.__api_url = self.API_PRACTICE_URL

        self.session = self._init_session()

    def _init_session(self):
        session = requests.session()
        session.headers.update({"Content-Type": "application/json",
                                "Accept-Datetime-Format": "UNIX",
                                'Authorization': 'Bearer {}'.format(self.__api_key)})
        return session

    def _send_request(self, method, url, params=None, data=None):
        if not params:
            params = OrderedDict()
        else:
            assert isinstance(params, OrderedDict)

        if not data:
            data = OrderedDict()
        else:
            assert isinstance(data, OrderedDict)

        response = getattr(self.session, method)(url, params=params, data=json.dumps(data))
        return response.json()

    """
    Account Endpoints
    """

    def get_all_accounts(self):
        endpoint = '/v3/accounts'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account(self, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)

        endpoint = f'/v3/accounts/{accountid}'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account_summary(self, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/summary'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account_instruments(self, instrument: str = None, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/instruments'

        params = OrderedDict()
        if instrument is not None:
            params["instruments"] = instrument

        return self._send_request('get', self.__api_url + endpoint, params)

    def get_account_changes(self, sinceTransactionID: str, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/changes'

        params = OrderedDict()
        params["sinceTransactionID"] = sinceTransactionID

        return self._send_request('get', self.__api_url + endpoint, params=params)

    def patch_account_configuration(self, alias: str, marginRate: float, accountid: str):
        # Client-defined alias (name) for the Account
        # alias: (string),
        # The string representation of a decimal number.
        # marginRate: (DecimalNumber)
        if accountid is None:
            accountid = self.default_account

        assert isinstance(accountid, str)
        assert isinstance(alias, str)
        assert isinstance(marginRate, float)
        endpoint = f'/v3/accounts/{accountid}/configuration'

        data = OrderedDict()
        data["alias"] = alias
        data["marginRate"] = marginRate

        return self._send_request('patch', self.__api_url + endpoint, data=data)

    """
    Instrument Endpoints
    """

    def get_candles_by_startend(self, instrument: str, granularity: str, from_unix: float, to_unix: float):
        endpoint = f'/v3/instruments/{instrument}/candles'
        params = OrderedDict()
        params["granularity"] = granularity
        params["from"] = str(from_unix)
        params["to"] = str(to_unix)

        return self._send_request('get', self.__api_url + endpoint, params=params)

    def get_last_k_candles(self, instrument: str, granularity: str, to_unix: [int, float], count: int):
        endpoint = f'/v3/instruments/{instrument}/candles'
        params = OrderedDict()
        params["granularity"] = granularity
        params["count"] = count
        params["to"] = str(to_unix)

        return self._send_request('get', self.__api_url + endpoint, params=params)

    def get_order_book(self, instrument: str):
        assert isinstance(instrument, str)
        endpoint = f'/v3/instruments/{instrument}/orderBook'
        return self._send_request('get', self.__api_url + endpoint)

    def get_position_book(self, instrument: str):
        assert isinstance(instrument, str)
        endpoint = f'/v3/instruments/{instrument}/positionBook'
        return self._send_request('get', self.__api_url + endpoint)

    """
    Order Endpoints
    """

    def get_orders(self, instrument: str, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/orders'

        params = OrderedDict()
        params["instrument"] = instrument
        params["count"] = 500

        return self._send_request('get', self.__api_url + endpoint,  params=params)

    def get_all_open_orders(self, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/pendingOrders'
        return self._send_request('get', self.__api_url + endpoint)

    @api_error_handler
    def get_order(self, orderid: str, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/orders/{orderid}'
        return self._send_request('get', self.__api_url + endpoint)

    @api_error_handler
    def cancel_order(self, orderid: str, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/orders/{orderid}/cancel'
        return self._send_request('put', self.__api_url + endpoint)

    def place_market_order(self, instrument: str, units: float, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/orders'

        order_request = {
            "type": "MARKET",
            "instrument": instrument,
            "units": units,
            "timeInForce": "FOK"
        }
        data = OrderedDict()
        data["order"] = order_request

        return self._send_request('post', self.__api_url + endpoint, data=data)

    def place_limit_order(self, instrument: str, units: float, price: float, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/orders'

        order_request = {
            "type": "LIMIT",
            "instrument": instrument,
            "units": units,
            "price": price,
            "timeInForce": "GTC"
        }
        data = OrderedDict()
        data["order"] = order_request

        return self._send_request('post', self.__api_url + endpoint, data=data)

    """
    Trade Endpoints
    """

    """
    Position Endpoints
    """

    def get_all_positions(self, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/positions'
        return self._send_request('get', self.__api_url + endpoint)

    def get_all_open_positions(self, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/openPositions'
        return self._send_request('get', self.__api_url + endpoint)

    def get_position(self, instrument: str, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/positions/{instrument}'
        return self._send_request('get', self.__api_url + endpoint)

    def close_position(self, instrument: str, accountid: str = None):
        if accountid is None:
            accountid = self.default_account
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/positions/{instrument}/close'
        return self._send_request('put', self.__api_url + endpoint)

    """
    Transaction Endpoints
    """

    """
    Pricing Endpoints
    """
