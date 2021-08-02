from blankly.exchanges.interfaces.oanda.oanda_auth import OandaAuth
import requests
from collections import OrderedDict
from urllib.parse import urlencode


class OandaAPI:
    # documentation here: http://developer.oanda.com/rest-live-v20/account-ep/
    API_URL = 'https://api-fxtrade.oanda.com'
    API_PRACTICE_URL = 'https://api-fxpractice.oanda.com'

    def __init__(self, auth: OandaAuth, sandbox: bool = False):
        self.api_key = auth.keys['PERSONAL_ACCESS_TOKEN']

        if not sandbox:
            self.__api_url = self.API_URL
        else:
            self.__api_url = self.API_PRACTICE_URL

        self.session = self._init_session()

    def _init_session(self):
        session = requests.session()
        session.headers.update({"Content-Type": "application/json",
                                "Accept-Datetime-Format": "UNIX",
                                'Authorization': 'Bearer {}'.format(self.api_key)})
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

        response = getattr(self.session, method)(url, params=params, data=data)
        return response.json()

    """
    Account Endpoints
    """

    def get_all_accounts(self):
        endpoint = '/v3/accounts'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account(self, accountid: str):
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account_summary(self, accountid: str):
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/summary'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account_instruments(self, accountid: str):
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/instruments'
        return self._send_request('get', self.__api_url + endpoint)

    def get_account_changes(self, accountid: str, sinceTransactionID: str):
        assert isinstance(accountid, str)
        endpoint = f'/v3/accounts/{accountid}/changes'

        params = OrderedDict()
        params["sinceTransactionID"] = sinceTransactionID

        return self._send_request('get', self.__api_url + endpoint, params=params)

    def patch_account_configuration(self, accountid: str, alias: str, marginRate: float):
        # Client-defined alias (name) for the Account
        # alias: (string),
        # The string representation of a decimal number.
        # marginRate: (DecimalNumber)

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
    def get_candles(self, instrument: str):
        endpoint = f'/v3/instruments/{instrument}/candles'
        return self._send_request('get', self.__api_url + endpoint)

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

    """
    Trade Endpoints
    """

    """
    Position Endpoints
     """

    """
    Transaction Endpoints
    """

    """
    Pricing Endpoints
    """

    """
    Forex Labs Endpoints
    """
