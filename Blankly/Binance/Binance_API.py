"""
    Calls to the Binance API.
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

import hashlib
import requests
import hmac
import time
from operator import itemgetter

from binance.client import Client

class API:
    def __init__(self, API_KEY, API_SECRET, requests_params=None, tld='com'):
        self.authenticated_client = Client(API_KEY, API_SECRET, tld=tld)


    def get_products(self):
        """
        Return list of products currently listed on Binance

        Use get_exchange_info() call instead

        :returns: list - List of product dictionaries
        {
          "s": "WRXUSDT",
          "st": "TRADING",
          "b": "WRX",
          "q": "USDT",
          "ba": "",
          "qa": "",
          "i": 0.1,
          "ts": 1e-05,
          "an": "WazirX",
          "qn": "TetherUS",
          "o": 0.57398,
          "h": 0.955,
          "l": 0.55362,
          "c": 0.81143,
          "v": 179068359.9,
          "qv": 141730637.189914,
          "y": 0,
          "as": 179068359.9,
          "pm": "USD\u24c8",
          "pn": "USD\u24c8",
          "cs": 186821429,
          "tags": [],
          "pom": false,
          "pomt": null,
          "etf": false
        },
        """
        return self.authenticated_client.get_products()

    def get_trade_fee(self):
        return self.authenticated_client.get_trade_fee()

    def get_klines(self, symbol, start_time=None, end_time=None):
        return self.authenticated_client.get_klines(symbol=symbol, start_time=None, end_time=None)


    # API_URL = 'https://api.binance.{}/api'
    # WITHDRAW_API_URL = 'https://api.binance.{}/wapi'
    # MARGIN_API_URL = 'https://api.binance.{}/sapi'
    # WEBSITE_URL = 'https://www.binance.{}'
    # FUTURES_URL = 'https://fapi.binance.{}/fapi'
    # PUBLIC_API_VERSION = 'v1'
    # PRIVATE_API_VERSION = 'v3'
    # WITHDRAW_API_VERSION = 'v3'
    # MARGIN_API_VERSION = 'v1'
    # FUTURES_API_VERSION = 'v1'
    #
    # SYMBOL_TYPE_SPOT = 'SPOT'
    #
    # ORDER_STATUS_NEW = 'NEW'
    # ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    # ORDER_STATUS_FILLED = 'FILLED'
    # ORDER_STATUS_CANCELED = 'CANCELED'
    # ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
    # ORDER_STATUS_REJECTED = 'REJECTED'
    # ORDER_STATUS_EXPIRED = 'EXPIRED'
    #
    # KLINE_INTERVAL_1MINUTE = '1m'
    # KLINE_INTERVAL_3MINUTE = '3m'
    # KLINE_INTERVAL_5MINUTE = '5m'
    # KLINE_INTERVAL_15MINUTE = '15m'
    # KLINE_INTERVAL_30MINUTE = '30m'
    # KLINE_INTERVAL_1HOUR = '1h'
    # KLINE_INTERVAL_2HOUR = '2h'
    # KLINE_INTERVAL_4HOUR = '4h'
    # KLINE_INTERVAL_6HOUR = '6h'
    # KLINE_INTERVAL_8HOUR = '8h'
    # KLINE_INTERVAL_12HOUR = '12h'
    # KLINE_INTERVAL_1DAY = '1d'
    # KLINE_INTERVAL_3DAY = '3d'
    # KLINE_INTERVAL_1WEEK = '1w'
    # KLINE_INTERVAL_1MONTH = '1M'
    #
    # SIDE_BUY = 'BUY'
    # SIDE_SELL = 'SELL'
    #
    # ORDER_TYPE_LIMIT = 'LIMIT'
    # ORDER_TYPE_MARKET = 'MARKET'
    # ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
    # ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    # ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    # ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    # ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'
    #
    # TIME_IN_FORCE_GTC = 'GTC'  # Good till cancelled
    # TIME_IN_FORCE_IOC = 'IOC'  # Immediate or cancel
    # TIME_IN_FORCE_FOK = 'FOK'  # Fill or kill
    #
    # ORDER_RESP_TYPE_ACK = 'ACK'
    # ORDER_RESP_TYPE_RESULT = 'RESULT'
    # ORDER_RESP_TYPE_FULL = 'FULL'
    #
    # # For accessing the data returned by Client.aggregate_trades().
    # AGG_ID = 'a'
    # AGG_PRICE = 'p'
    # AGG_QUANTITY = 'q'
    # AGG_FIRST_TRADE_ID = 'f'
    # AGG_LAST_TRADE_ID = 'l'
    # AGG_TIME = 'T'
    # AGG_BUYER_MAKES = 'm'
    # AGG_BEST_MATCH = 'M'
    #
    #
    #
    # def __init__(self, API_KEY, API_SECRET, requests_params=None, tld='com'):
    #     self.API_URL = self.API_URL.format(tld)
    #     self.WITHDRAW_API_URL = self.WITHDRAW_API_URL.format(tld)
    #     self.MARGIN_API_URL = self.MARGIN_API_URL.format(tld)
    #     self.WEBSITE_URL = self.WEBSITE_URL.format(tld)
    #     self.FUTURES_URL = self.FUTURES_URL.format(tld)
    #
    #     self.API_KEY = API_KEY
    #     self.API_SECRET = API_SECRET
    #     self.session = self._init_session()
    #     self._requests_params = requests_params
    #     self.response = None
    #
    #     # init DNS and SSL cert
    #     self.ping()
    #
    # def _init_session(self):
    #
    #     session = requests.session()
    #     session.headers.update({'Accept': 'application/json',
    #                             'User-Agent': 'binance/python',
    #                             'X-MBX-APIKEY': self.API_KEY})
    #     return session
    #
    # def _create_api_uri(self, path, signed=True, version=PUBLIC_API_VERSION):
    #     v = self.PRIVATE_API_VERSION if signed else version
    #     return self.API_URL + '/' + v + '/' + path
    #
    # def _create_withdraw_api_uri(self, path):
    #     return self.WITHDRAW_API_URL + '/' + self.WITHDRAW_API_VERSION + '/' + path
    #
    # def _create_margin_api_uri(self, path):
    #     return self.MARGIN_API_URL + '/' + self.MARGIN_API_VERSION + '/' + path
    #
    # def _create_website_uri(self, path):
    #     return self.WEBSITE_URL + '/' + path
    #
    # def _create_futures_api_uri(self, path):
    #     return self.FUTURES_URL + '/' + self.FUTURES_API_VERSION + '/' + path
    #
    # def _generate_signature(self, data):
    #
    #     ordered_data = self._order_params(data)
    #     query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
    #     m = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
    #     return m.hexdigest()
    #
    # def _order_params(self, data):
    #     """Convert params to list with signature as last element
    #
    #     :param data:
    #     :return:
    #
    #     """
    #     has_signature = False
    #     params = []
    #     for key, value in data.items():
    #         if key == 'signature':
    #             has_signature = True
    #         else:
    #             params.append((key, value))
    #     # sort parameters by key
    #     params.sort(key=itemgetter(0))
    #     if has_signature:
    #         params.append(('signature', data['signature']))
    #     return params
    #
    # def _request(self, method, uri, signed, force_params=False, **kwargs):
    #
    #     # set default requests timeout
    #     kwargs['timeout'] = 10
    #
    #     # add our global requests params
    #     if self._requests_params:
    #         kwargs.update(self._requests_params)
    #
    #     data = kwargs.get('data', None)
    #     if data and isinstance(data, dict):
    #         kwargs['data'] = data
    #
    #         # find any requests params passed and apply them
    #         if 'requests_params' in kwargs['data']:
    #             # merge requests params into kwargs
    #             kwargs.update(kwargs['data']['requests_params'])
    #             del(kwargs['data']['requests_params'])
    #
    #     if signed:
    #         # generate signature
    #         kwargs['data']['timestamp'] = int(time.time() * 1000)
    #         kwargs['data']['signature'] = self._generate_signature(kwargs['data'])
    #
    #     # sort get and post params to match signature order
    #     if data:
    #         # sort post params
    #         kwargs['data'] = self._order_params(kwargs['data'])
    #         # Remove any arguments with values of None.
    #         null_args = [i for i, (key, value) in enumerate(kwargs['data']) if value is None]
    #         for i in reversed(null_args):
    #             del kwargs['data'][i]
    #
    #     # if get request assign data array to params value for requests lib
    #     if data and (method == 'get' or force_params):
    #         kwargs['params'] = '&'.join('%s=%s' % (data[0], data[1]) for data in kwargs['data'])
    #         del(kwargs['data'])
    #
    #     self.response = getattr(self.session, method)(uri, **kwargs)
    #     return self._handle_response()
    #
    # def _request_api(self, method, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
    #     uri = self._create_api_uri(path, signed, version)
    #
    #     return self._request(method, uri, signed, **kwargs)
    #
    # def _request_withdraw_api(self, method, path, signed=False, **kwargs):
    #     uri = self._create_withdraw_api_uri(path)
    #
    #     return self._request(method, uri, signed, True, **kwargs)
    #
    # def _request_margin_api(self, method, path, signed=False, **kwargs):
    #     uri = self._create_margin_api_uri(path)
    #
    #     return self._request(method, uri, signed, **kwargs)
    #
    # def _request_website(self, method, path, signed=False, **kwargs):
    #     uri = self._create_website_uri(path)
    #
    #     return self._request(method, uri, signed, **kwargs)
    #
    # def _request_futures_api(self, method, path, signed=False, **kwargs):
    #     uri = self._create_futures_api_uri(path)
    #
    #     return self._request(method, uri, signed, True, **kwargs)
    #
    # def _handle_response(self):
    #     """Internal helper for handling API responses from the Binance server.
    #     Raises the appropriate exceptions when necessary; otherwise, returns the
    #     response.
    #     """
    #     if not str(self.response.status_code).startswith('2'):
    #         raise BinanceAPIException(self.response)
    #     try:
    #         return self.response.json()
    #     except ValueError:
    #         raise BinanceRequestException('Invalid Response: %s' % self.response.text)
    #
    # def _get(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
    #     return self._request_api('get', path, signed, version, **kwargs)
    #
    # def _post(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
    #     return self._request_api('post', path, signed, version, **kwargs)
    #
    # def _put(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
    #     return self._request_api('put', path, signed, version, **kwargs)
    #
    # def _delete(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
    #     return self._request_api('delete', path, signed, version, **kwargs)
    #
    # def get_products(self):
    #     """Return list of products currently listed on Binance
    #
    #     Use get_exchange_info() call instead
    #
    #     :returns: list - List of product dictionaries
    #
    #     :raises: BinanceRequestException, BinanceAPIException
    #
    #     """
    #     products = self._request_website('get', 'exchange-api/v1/public/asset-service/product/get-products')
    #     return products
