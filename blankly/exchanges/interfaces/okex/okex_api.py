import requests

import hmac
import base64
import datetime
import json

API_URL = 'https://www.okex.com'

CONTENT_TYPE = 'Content-Type'
OK_ACCESS_KEY = 'OK-ACCESS-KEY'
OK_ACCESS_SIGN = 'OK-ACCESS-SIGN'
OK_ACCESS_TIMESTAMP = 'OK-ACCESS-TIMESTAMP'
OK_ACCESS_PASSPHRASE = 'OK-ACCESS-PASSPHRASE'

ACEEPT = 'Accept'
COOKIE = 'Cookie'
LOCALE = 'Locale='

APPLICATION_JSON = 'application/json'

GET = "GET"
POST = "POST"
DELETE = "DELETE"

SERVER_TIMESTAMP_URL = '/api/general/v3/time'

# account
WALLET_INFO = '/api/account/v3/wallet'
CURRENCY_INFO = '/api/account/v3/wallet/'
COIN_TRANSFER = '/api/account/v3/transfer'
GET_STATE = '/api/account/v3/transfer/state'
COIN_WITHDRAW = '/api/account/v3/withdrawal'
LEDGER_RECORD = '/api/account/v3/ledger'
TOP_UP_ADDRESS = '/api/account/v3/deposit/address'
ASSET_VALUATION = '/api/account/v3/asset-valuation'
SUB_ACCOUNT = '/api/account/v3/sub-account'
COINS_WITHDRAW_RECORD = '/api/account/v3/withdrawal/history'
COIN_WITHDRAW_RECORD = '/api/account/v3/withdrawal/history/'
COIN_TOP_UP_RECORDS = '/api/account/v3/deposit/history'
COIN_TOP_UP_RECORD = '/api/account/v3/deposit/history/'
CURRENCIES_INFO = '/api/account/v3/currencies'
COIN_FEE = '/api/account/v3/withdrawal/fee'
GET_UID = '/api/account/v3/uid'
PURCHASE_REDEMPT = '/api/account/v3/purchase_redempt'

# spot
SPOT_ACCOUNT_INFO = '/api/spot/v3/accounts'
SPOT_COIN_ACCOUNT_INFO = '/api/spot/v3/accounts/'
SPOT_LEDGER_RECORD = '/api/spot/v3/accounts/'
SPOT_ORDER = '/api/spot/v3/orders'
SPOT_ORDERS = '/api/spot/v3/batch_orders'
SPOT_REVOKE_ORDER = '/api/spot/v3/cancel_orders/'
SPOT_REVOKE_ORDERS = '/api/spot/v3/cancel_batch_orders/'
SPOT_RAMEND_ORDER = '/api/spot/v3/amend_order'
SPOT_AMEND_BATCH_ORDERS = '/api/spot/v3/amend_batch_orders'
SPOT_ORDERS_LIST = '/api/spot/v3/orders'
SPOT_ORDERS_PENDING = '/api/spot/v3/orders_pending'
SPOT_ORDER_INFO = '/api/spot/v3/orders/'
SPOT_FILLS = '/api/spot/v3/fills'
SPOT_ORDER_ALGO = '/api/spot/v3/order_algo'
SPOT_CANCEL_ALGOS = '/api/spot/v3/cancel_batch_algos'
SPOT_TRADE_FEE = '/api/spot/v3/trade_fee'
SPOT_GET_ORDER_ALGOS = '/api/spot/v3/algo'
SPOT_COIN_INFO = '/api/spot/v3/instruments'
SPOT_DEPTH = '/api/spot/v3/instruments/'
SPOT_TICKER = '/api/spot/v3/instruments/ticker'
SPOT_SPECIFIC_TICKER = '/api/spot/v3/instruments/'
SPOT_DEAL = '/api/spot/v3/instruments/'
SPOT_KLINE = '/api/spot/v3/instruments/'

# lever
LEVER_ACCOUNT = '/api/margin/v3/accounts'
LEVER_COIN_ACCOUNT = '/api/margin/v3/accounts/'
LEVER_LEDGER_RECORD = '/api/margin/v3/accounts/'
LEVER_SET_LEVERAGE = '/api/margin/v3/instruments/'
LEVER_CONFIG = '/api/margin/v3/accounts/availability'
LEVER_SPECIFIC_CONFIG = '/api/margin/v3/accounts/'
LEVER_BORROW_RECORD = '/api/margin/v3/accounts/borrowed'
LEVER_SPECIFIC_BORROW_RECORD = '/api/margin/v3/accounts/'
LEVER_BORROW_COIN = '/api/margin/v3/accounts/borrow'
LEVER_REPAYMENT_COIN = '/api/margin/v3/accounts/repayment'
LEVER_ORDER = '/api/margin/v3/orders'
LEVER_ORDERS = '/api/margin/v3/batch_orders'
LEVEL_AMEND_ORDER = '/api/margin/v3/amend_order/'
LEVEL_AMEND_BATCH_ORDERS = '/api/margin/v3/amend_batch_orders/'
LEVER_REVOKE_ORDER = '/api/margin/v3/cancel_orders/'
LEVER_REVOKE_ORDERS = '/api/margin/v3/cancel_batch_orders'
LEVER_ORDER_LIST = '/api/margin/v3/orders'
LEVEL_ORDERS_PENDING = '/api/margin/v3/orders_pending'
LEVER_ORDER_INFO = '/api/margin/v3/orders/'
LEVER_FILLS = '/api/margin/v3/fills'
LEVER_MARK_PRICE = '/api/margin/v3/instruments/'

# future
FUTURE_POSITION = '/api/futures/v3/position'
FUTURE_SPECIFIC_POSITION = '/api/futures/v3/'
FUTURE_ACCOUNTS = '/api/futures/v3/accounts'
FUTURE_COIN_ACCOUNT = '/api/futures/v3/accounts/'
FUTURE_GET_LEVERAGE = '/api/futures/v3/accounts/'
FUTURE_SET_LEVERAGE = '/api/futures/v3/accounts/'
FUTURE_LEDGER = '/api/futures/v3/accounts/'
FUTURE_ORDER = '/api/futures/v3/order'
FUTURE_ORDERS = '/api/futures/v3/orders'
FUTURE_REVOKE_ORDER = '/api/futures/v3/cancel_order/'
FUTURE_REVOKE_ORDERS = '/api/futures/v3/cancel_batch_orders/'
FUTURE_ORDERS_LIST = '/api/futures/v3/orders/'
FUTURE_ORDER_INFO = '/api/futures/v3/orders/'
FUTURE_FILLS = '/api/futures/v3/fills'
FUTURE_MARGIN_MODE = '/api/futures/v3/accounts/margin_mode'
FUTURE_CLOSE_POSITION = '/api/futures/v3/close_position'
FUTURE_CANCEL_ALL = '/api/futures/v3/cancel_all'
HOLD_AMOUNT = '/api/futures/v3/accounts/'
FUTURE_ORDER_ALGO = '/api/futures/v3/order_algo'
FUTURE_CANCEL_ALGOS = '/api/futures/v3/cancel_algos'
FUTURE_GET_ORDER_ALGOS = '/api/futures/v3/order_algo/'
FUTURE_TRADE_FEE = '/api/futures/v3/trade_fee'
FUTURE_PRODUCTS_INFO = '/api/futures/v3/instruments'
FUTURE_DEPTH = '/api/futures/v3/instruments/'
FUTURE_TICKER = '/api/futures/v3/instruments/ticker'
FUTURE_SPECIFIC_TICKER = '/api/futures/v3/instruments/'
FUTURE_TRADES = '/api/futures/v3/instruments/'
FUTURE_KLINE = '/api/futures/v3/instruments/'
FUTURE_INDEX = '/api/futures/v3/instruments/'
FUTURE_RATE = '/api/futures/v3/rate'
FUTURE_ESTIMAT_PRICE = '/api/futures/v3/instruments/'
FUTURE_HOLDS = '/api/futures/v3/instruments/'
FUTURE_LIMIT = '/api/futures/v3/instruments/'
FUTURE_MARK = '/api/futures/v3/instruments/'
FUTURE_LIQUIDATION = '/api/futures/v3/instruments/'
FUTURE_AUTO_MARGIN = '/api/futures/v3/accounts/auto_margin'
FUTURE_CHANGE_MARGIN = '/api/futures/v3/position/margin'
FUTURE_HISTORY_SETTLEMENT = '/api/futures/v3/settlement/history'
FUTURE_AMEND_ORDER = '/api/futures/v3/amend_order/'
FUTURE_AMEND_BATCH_ORDERS = '/api/futures/v3/amend_batch_orders/'

# swap
SWAP_POSITIONS = '/api/swap/v3/position'
SWAP_POSITION = '/api/swap/v3/'
SWAP_ACCOUNTS = '/api/swap/v3/accounts'
SWAP_ORDER_ALGO = '/api/swap/v3/order_algo'
SWAP_CANCEL_ALGOS = '/api/swap/v3/cancel_algos'
SWAP_GET_ORDER_ALGOS = '/api/swap/v3/order_algo/'
SWAP_GET_TRADE_FEE = '/api/swap/v3/trade_fee'
SWAP_ACCOUNT = '/api/swap/v3/'
SWAP_ORDER = '/api/swap/v3/order'
SWAP_ORDERS = '/api/swap/v3/orders'
SWAP_CANCEL_ORDER = '/api/swap/v3/cancel_order/'
SWAP_CANCEL_ORDERS = '/api/swap/v3/cancel_batch_orders/'
SWAP_FILLS = '/api/swap/v3/fills'
SWAP_INSTRUMENTS = '/api/swap/v3/instruments'
SWAP_TICKETS = '/api/swap/v3/instruments/ticker'
SWAP_RATE = '/api/swap/v3/rate'
SWAP_CLOSE_POSITION = '/api/swap/v3/close_position'
SWAP_CANCEL_ALL = '/api/swap/v3/cancel_all'
SWAP_AMEND_ORDER = '/api/swap/v3/amend_order/'
SWAP_AMEND_BATCH_ORDERS = '/api/swap/v3/amend_batch_orders/'
SWAP_HISTORY_KLINE = '/api/swap/v3/instruments/'

# information
INFORMATION = '/api/information/v3/'

# index
INDEX_GET_CONSTITUENTS = '/api/index/v3/'

# option
OPTION_ORDER = '/api/option/v3/order'
OPTION_ORDERS = '/api/option/v3/orders'
OPTION_CANCEL_ORDER = '/api/option/v3/cancel_order/'
CANCEL_ALL = '/api/option/v3/cancel_all/'
OPTION_CANCEL_ORDERS = '/api/option/v3/cancel_batch_orders/'
OPTION_AMEND_ORDER = '/api/option/v3/amend_order/'
OPTION_AMEND_BATCH_ORDERS = '/api/option/v3/amend_batch_orders/'
OPTION_FILLS = '/api/option/v3/fills/'
OPTION_POSITION = '/api/option/v3/'
OPTION_ACCOUNT = '/api/option/v3/accounts/'
OPTION_TRADE_FEE = '/api/option/v3/trade_fee'
SET_GREEKS = '/api/option/v3/set-greeks'
OPTION_INDEX = '/api/option/v3/underlying'
OPTION_INSTRUMENTS = '/api/option/v3/instruments/'
OPTION_HISTORY_SETTLEMENT = '/api/option/v3/settlement/history/'

# system
SYSTEM_STATUS = '/api/system/v3/status'

# oracle
GET_ORACLE = '/api/market/v3/oracle'


def sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)


def pre_hash(timestamp, method, request_path, body):
    print('pre_hash:', str(timestamp) + str.upper(method) + request_path + body)
    return str(timestamp) + str.upper(method) + request_path + body


def get_header(api_key, sign_, timestamp, passphrase):
    header = dict()
    header[CONTENT_TYPE] = APPLICATION_JSON
    header[OK_ACCESS_KEY] = api_key
    header[OK_ACCESS_SIGN] = sign_
    header[OK_ACCESS_TIMESTAMP] = str(timestamp)
    header[OK_ACCESS_PASSPHRASE] = passphrase

    return header


def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'

    return url[0:-1]


def get_timestamp():
    now = datetime.datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def signature(timestamp, method, request_path, body, secret_key):
    if str(body) == '{}' or str(body) == 'None':
        body = ''
    message = str(timestamp) + str.upper(method) + request_path + str(body)
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)


class OkexAPIException(Exception):

    def __init__(self, response):
        print(response.text + ', ' + str(response.status_code))
        self.code = 0
        try:
            json_res = response.json()
        except ValueError:
            self.message = 'Invalid JSON error message from Okex: {}'.format(response.text)
        else:
            if "error_code" in json_res.keys() and "error_message" in json_res.keys():
                self.code = json_res['error_code']
                self.message = json_res['error_message']
            else:
                self.code = 'None'
                self.message = 'System error'

        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        return 'API Request Error(error_code=%s): %s' % (self.code, self.message)


class OkexRequestException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'OkexRequestException: %s' % self.message


class OkexParamsException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'OkexParamsException: %s' % self.message


class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, first=False):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.first = first
        self.test = test

    def _request(self, method, request_path, params, cursor=False):
        if method == GET:
            request_path = request_path + parse_params_to_str(params)
        # url
        url = API_URL + request_path

        # 获取本地时间
        timestamp = get_timestamp()

        # sign & header
        if self.use_server_time:
            # 获取服务器时间
            timestamp = self._get_timestamp()

        body = json.dumps(params) if method == POST else ""
        sign_ = sign(pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = get_header(self.API_KEY, sign_, timestamp, self.PASSPHRASE)

        if self.test:
            header['x-simulated-trading'] = '1'
        if self.first:
            print("url:", url)
            self.first = False

        print("url:", url)
        print("headers:", header)
        print("body:", body)

        # send request
        response = None
        if method == GET:
            response = requests.get(url, headers=header)
        elif method == POST:
            response = requests.post(url, data=body, headers=header)
        elif method == DELETE:
            response = requests.delete(url, headers=header)

        # exception handle
        if not str(response.status_code).startswith('2'):
            raise OkexAPIException(response)
        try:
            res_header = response.headers
            if cursor:
                r = dict()
                try:
                    r['before'] = res_header['OK-BEFORE']
                    r['after'] = res_header['OK-AFTER']
                except Exception:
                    pass
                return response.json(), r
            else:
                return response.json()

        except ValueError:
            raise OkexRequestException('Invalid Response: %s' % response.text)

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params, cursor=False):
        return self._request(method, request_path, params, cursor)

    @staticmethod
    def _get_timestamp():
        url = API_URL + SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['iso']
        else:
            return ""


class SpotAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, first=False):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, test, first)

    # query spot account info
    def get_account_info(self):
        return self._request_without_params(GET, SPOT_ACCOUNT_INFO)

    # query specific coin account info
    def get_coin_account_info(self, currency):
        return self._request_without_params(GET, SPOT_COIN_ACCOUNT_INFO + str(currency))

    # query ledger record not paging
    def get_ledger_record(self, currency, after='', before='', limit='', type_=''):
        params = {}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
        if type_:
            params['type'] = type_
        return self._request_with_params(GET, SPOT_LEDGER_RECORD + str(currency) + '/ledger', params, cursor=True)

    # take order
    def take_order(self, instrument_id, side, client_oid='', type_='', size='', price='', order_type='0', notional=''):
        params = {'instrument_id': instrument_id, 'side': side, 'client_oid': client_oid, 'type': type_, 'size': size,
                  'price': price, 'order_type': order_type, 'notional': notional}
        return self._request_with_params(POST, SPOT_ORDER, params)

    def take_orders(self, params):
        return self._request_with_params(POST, SPOT_ORDERS, params)

    # revoke order
    def revoke_order(self, instrument_id, order_id='', client_oid=''):
        params = {'instrument_id': instrument_id}
        if order_id:
            return self._request_with_params(POST, SPOT_REVOKE_ORDER + str(order_id), params)
        elif client_oid:
            return self._request_with_params(POST, SPOT_REVOKE_ORDER + str(client_oid), params)

    def revoke_orders(self, params):
        return self._request_with_params(POST, SPOT_REVOKE_ORDERS, params)

    # amend order
    def amend_order(self, instrument_id, cancel_on_fail, order_id='', client_oid='', request_id='', new_size='',
                    new_price=''):
        params = {'instrument_id': instrument_id, 'cancel_on_fail': cancel_on_fail}
        if order_id:
            params['order_id'] = order_id
        if client_oid:
            params['client_oid'] = client_oid
        if request_id:
            params['request_id'] = request_id
        if order_id:
            params['order_id'] = order_id
        if new_size:
            params['new_size'] = new_size
        if new_price:
            params['new_price'] = new_price
        return self._request_with_params(POST, SPOT_RAMEND_ORDER + str(instrument_id), params)

    # amend batch orders
    def amend_batch_orders(self, params):
        return self._request_with_params(POST, SPOT_AMEND_BATCH_ORDERS, params)

    # query orders list v3
    def get_orders_list(self, instrument_id, state, after='', before='', limit=''):
        params = {'instrument_id': instrument_id, 'state': state}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_ORDERS_LIST, params, cursor=True)

    # query order info
    def get_order_info(self, instrument_id, order_id='', client_oid=''):
        params = {'instrument_id': instrument_id}
        if order_id:
            return self._request_with_params(GET, SPOT_ORDER_INFO + str(order_id), params)
        elif client_oid:
            return self._request_with_params(GET, SPOT_ORDER_INFO + str(client_oid), params)

    def get_orders_pending(self, instrument_id, after='', before='', limit=''):
        params = {'instrument_id': instrument_id}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_ORDERS_PENDING, params, cursor=True)

    def get_fills(self, instrument_id, order_id='', after='', before='', limit=''):
        params = {'instrument_id': instrument_id}
        if order_id:
            params['order_id'] = order_id
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_FILLS, params, cursor=True)

    # take order_algo
    def take_order_algo(self, instrument_id, mode, order_type, size, side, trigger_price='', algo_price='',
                        algo_type='',
                        callback_rate='', algo_variance='', avg_amount='', limit_price='', sweep_range='',
                        sweep_ratio='', single_limit='', time_interval='', tp_trigger_price='', tp_price='',
                        tp_trigger_type='', sl_trigger_type='', sl_trigger_price='', sl_price='', ):
        params = {'instrument_id': instrument_id, 'mode': mode, 'order_type': order_type, 'size': size, 'side': side}
        if order_type == '1':  # 计划委托参数
            params['trigger_price'] = trigger_price
            params['algo_price'] = algo_price
            if algo_type:
                params['algo_type'] = algo_type
        elif order_type == '2':  # 跟踪委托参数
            params['callback_rate'] = callback_rate
            params['trigger_price'] = trigger_price
        elif order_type == '3':  # 冰山委托参数（最多同时存在6单）
            params['algo_variance'] = algo_variance
            params['avg_amount'] = avg_amount
            params['limit_price'] = limit_price
        elif order_type == '4':  # 时间加权参数（最多同时存在6单）
            params['sweep_range'] = sweep_range
            params['sweep_ratio'] = sweep_ratio
            params['single_limit'] = single_limit
            params['limit_price'] = limit_price
            params['time_interval'] = time_interval
        elif order_type == '5':  # 止盈止损参数（最多同时存在6单）
            if tp_trigger_type:
                params['tp_trigger_type'] = tp_trigger_type
            if tp_trigger_price:
                params['tp_trigger_price'] = tp_trigger_price
            if tp_price:
                params['tp_price'] = tp_price
            if sl_price:
                params['sl_price'] = sl_price
            if sl_trigger_price:
                params['sl_trigger_price'] = sl_trigger_price
            if sl_trigger_type:
                params['sl_trigger_type'] = sl_trigger_type
        return self._request_with_params(POST, SPOT_ORDER_ALGO, params)

    # cancel_algos
    def cancel_algos(self, instrument_id, algo_ids, order_type):
        params = {'instrument_id': instrument_id, 'algo_ids': algo_ids, 'order_type': order_type}
        return self._request_with_params(POST, SPOT_CANCEL_ALGOS, params)

    def get_trade_fee(self):
        return self._request_without_params(GET, SPOT_TRADE_FEE)

    # get order_algos
    def get_order_algos(self, instrument_id, order_type, status='', algo_id='', before='', after='', limit=''):
        params = {'instrument_id': instrument_id, 'order_type': order_type}
        if status:
            params['status'] = status
        elif algo_id:
            params['algo_id'] = algo_id
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_GET_ORDER_ALGOS, params)

    # query spot coin info
    def get_coin_info(self):
        return self._request_without_params(GET, SPOT_COIN_INFO)

    # query depth
    def get_depth(self, instrument_id, size='', depth=''):
        params = {}
        if size:
            params['size'] = size
        if depth:
            params['depth'] = depth
        return self._request_with_params(GET, SPOT_DEPTH + str(instrument_id) + '/book', params)

    # query ticker info
    def get_ticker(self):
        return self._request_without_params(GET, SPOT_TICKER)

    # query specific ticker
    def get_specific_ticker(self, instrument_id):
        return self._request_without_params(GET, SPOT_SPECIFIC_TICKER + str(instrument_id) + '/ticker')

    def get_deal(self, instrument_id, limit=''):
        params = {}
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_DEAL + str(instrument_id) + '/trades', params)

    # query k-line info
    def get_kline(self, instrument_id, start='', end='', granularity=''):
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if granularity:
            params['granularity'] = granularity
        # 按时间倒叙 即由结束时间到开始时间
        return self._request_with_params(GET, SPOT_KLINE + str(instrument_id) + '/candles', params)

        # 按时间正序 即由开始时间到结束时间
        # data = self._request_with_params(GET, SPOT_KLINE + str(instrument_id) + '/candles', params)
        # return list(reversed(data))

    def get_history_kline(self, instrument_id, start='', end='', granularity=''):
        params = {}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if granularity:
            params['granularity'] = granularity
        return self._request_with_params(GET, SPOT_KLINE + str(instrument_id) + '/history' + '/candles', params)
