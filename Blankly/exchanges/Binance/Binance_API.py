"""
    Unused Binance API calls.
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
import base64
import hashlib
import hmac
import requests
import time
import warnings
import json
from urllib.parse import urlencode
import typing
from requests.auth import AuthBase
import binance
from collections import OrderedDict


# Create custom authentication for Exchange
class BinanceExchangeAuth(AuthBase):
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, request):
        request.headers['X-MBX-APIKEY'] = self.api_key.encode("utf-8")
        request.headers['Content-Type'] = 'application/json;charset=utf-8'
        return request


def hmac_encode(message: str, secret_key: str) -> str:
    assert isinstance(message, str)
    assert isinstance(secret_key, str)
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return signature.hexdigest()


class API:
    def __init__(self, API_KEY, API_SECRET, API_URL='https://testnet.binance.vision'):
        self.api_key = API_KEY
        self.secret_key = API_SECRET
        self.__auth = BinanceExchangeAuth(API_KEY)
        self.__api_url = API_URL
        self.session = self._init_session()

    def _init_session(self):
        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                                'X-MBX-APIKEY': self.api_key.encode('utf-8')})
        return session

    def _send_request(self, method, url, signed, params=None, data=None):
        if not params:
            params = OrderedDict()
        else:
            assert isinstance(params, OrderedDict)

        if not data:
            data = OrderedDict()
        else:
            assert isinstance(data, OrderedDict)

        params["timestamp"] = int(time.time() * 1000)

        if signed:
            msg = urlencode(params) + urlencode(data)
            params["signature"] = hmac_encode(msg, self.secret_key)

        response = getattr(self.session, method)(url, params=params, data=data)
        return response.json()

    ## wallet endpoints ###
    def system_status(self):
        endpoint = '/wapi/v3/systemStatus.html'
        SIGNED = False
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def all_coins(self):
        endpoint = "/sapi/v1/capital/config/getall"
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def account_snapshot(self, type):
        endpoint = "/sapi/v1/accountSnapshot"
        params = OrderedDict()
        params["type"] = type
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params)

    def disable_fast_withdraw(self):
        endpoint = "/sapi/v1/account/disableFastWithdrawSwitch"
        SIGNED = True
        return self._send_request('post', self.__api_url + endpoint, SIGNED)

    def enable_fast_withdraw(self):
        endpoint = "/sapi/v1/account/enableFastWithdrawSwitch"
        SIGNED = True
        return self._send_request('post', self.__api_url + endpoint, SIGNED)

    def withdraw(self, asset, address, amount, **optional_params):
        endpoint = '/wapi/v3/withdraw.html'
        SIGNED = True
        params = OrderedDict()
        params["asset"] = asset
        params["address"] = address
        params["amount"] = amount
        params.update(optional_params)
        return self._send_request('post', self.__api_url + endpoint, SIGNED, params=params)

    def account_info(self):
        endpoint = '/api/v3/account'
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def withdraw_history(self, **optional_params):
        endpoint = '/wapi/v3/depositHistory.html'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def deposit_address(self, **optional_params):
        endpoint = '/wapi/v3/depositAddress.html'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def account_status(self):
        endpoint = '/wapi/v3/accountStatus.html'
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def trading_status(self):
        endpoint = '/wapi/v3/apiTradingStatus.html'
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def dust_log(self):
        endpoint = '/wapi/v3/userAssetDribbletLog.html'
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def dust_transfer(self):
        endpoint = '/sapi/v1/asset/dust'
        SIGNED = True
        return self._send_request('post', self.__api_url + endpoint, SIGNED)

    def dividend_record(self, **optional_params):
        endpoint = '/sapi/v1/asset/assetDividend'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def asset_detail(self, **optional_params):
        endpoint = '/sapi/v1/asset/assetDetail'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def trade_fee(self, **optional_params):
        endpoint = '/wapi/v3/tradeFee.html'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def universal_transfer(self, type, asset, amount):
        endpoint = '/wapi/v3/withdraw.html'
        SIGNED = True
        params = OrderedDict()
        params["type"] = type
        params["asset"] = asset
        params["amount"] = amount
        return self._send_request('post', self.__api_url + endpoint, SIGNED, params=params)

    def query_universal_transfer(self, type, **optional_params):
        endpoint = '/sapi/v1/asset/transfer'
        SIGNED = True
        params = OrderedDict()
        params["type"] = type
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    ## market data endpoints #######
    def test_connectivity(self):
        endpoint = '/api/v3/ping'
        SIGNED = False
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def check_server_time(self):
        endpoint = '/api/v3/time'
        SIGNED = False
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def exchange_information(self, symbol):
        endpoint = '/api/v3/exchangeInfo'
        SIGNED = False
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def order_book(self, symbol):
        endpoint = '/api/v3/depth'
        SIGNED = False
        params = OrderedDict()
        params["symbol"] = symbol
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def recent_trades_list(self, symbol):
        endpoint = '/api/v3/trades'
        SIGNED = False
        params = OrderedDict()
        params["symbol"] = symbol
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def old_trade_lookup(self, symbol, **optional_params):
        endpoint = '/api/v3/historicalTrades'
        SIGNED = False
        params = OrderedDict()
        params["symbol"] = symbol
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def compressed_trades_list(self, symbol, **optional_params):
        endpoint = '/api/v3/aggTrades'
        SIGNED = False
        params = OrderedDict()
        params["symbol"] = symbol
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def klines(self, symbol, interval, **optional_params):
        endpoint = '/api/v3/klines'
        SIGNED = False
        params = OrderedDict()
        params["symbol"] = symbol
        params["interval"] = interval
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def current_average_price(self, symbol):
        endpoint = '/api/v3/ticker/24hr'
        SIGNED = False
        params = OrderedDict()
        params["symbol"] = symbol
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def ticker_price_change_statistics(self, **optional_params):
        endpoint = '/api/v3/ticker/24hr'
        SIGNED = False
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def symbol_price_ticker(self, **optional_params):
        endpoint = '/api/v3/ticker/price'
        SIGNED = False
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def symbol_orderbook_ticker(self, **optional_params):
        endpoint = '/api/v3/ticker/bookTicker'
        SIGNED = False
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    ## spot account/trade endpoints #######
    def test_new_order(self, symbol, side, type, **optional_params):
        endpoint = '/api/v3/order/test'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params["side"] = side
        params["type"] = type
        params.update(optional_params)
        return self._send_request('post', self.__api_url + endpoint, SIGNED, params=params)

    def new_order(self, symbol, side, type, **optional_params):
        endpoint = '/api/v3/order'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params["side"] = side
        params["type"] = type
        params.update(optional_params)
        return self._send_request('post', self.__api_url + endpoint, SIGNED, params=params)

    def cancel_order(self, symbol, **optional_params):
        endpoint = '/api/v3/order'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params.update(optional_params)
        return self._send_request('delete', self.__api_url + endpoint, SIGNED, params=params)

    def cancel_all_open_orders(self, symbol):
        endpoint = 'api/v3/openOrders'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        return self._send_request('delete', self.__api_url + endpoint, SIGNED, params=params)

    def query_order(self, symbol):
        endpoint = '/api/v3/order'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def current_open_orders(self, **optional_params):
        endpoint = '/api/v3/openOrders'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def all_orders(self, symbol, **optional_params):
        endpoint = '/api/v3/allOrders'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def new_oco(self, symbol, side, quantity, price, stopPrice, **optional_params):
        endpoint = '/api/v3/order/oco'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params["side"] = side
        params["quantity"] = quantity
        params["price"] = price
        params["stopPrice"] = stopPrice
        params.update(optional_params)
        return self._send_request('post', self.__api_url + endpoint, SIGNED, params=params)

    def cancel_oco(self, symbol, **optional_params):
        endpoint = '/api/v3/orderList'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params.update(optional_params)
        return self._send_request('delete', self.__api_url + endpoint, SIGNED, params=params)

    def query_oco(self, **optional_params):
        endpoint = '/api/v3/orderList'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def query_all_oco(self, **optional_params):
        endpoint = '/api/v3/allOrderList'
        SIGNED = True
        params = OrderedDict()
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)

    def query_open_oco(self):
        endpoint = '/api/v3/openOrderList'
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def account_information(self):
        endpoint = '/api/v3/account'
        SIGNED = True
        return self._send_request('get', self.__api_url + endpoint, SIGNED)

    def account_trade_list(self, symbol,  **optional_params):
        endpoint = '/api/v3/myTrades'
        SIGNED = True
        params = OrderedDict()
        params["symbol"] = symbol
        params.update(optional_params)
        return self._send_request('get', self.__api_url + endpoint, SIGNED, params=params)
