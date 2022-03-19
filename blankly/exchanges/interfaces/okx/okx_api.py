import requests
import hmac
import base64
import datetime
# import time
import json

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

SERVER_TIMESTAMP_URL = '/api/v5/public/time'

# account
POSITION_RISK = '/api/v5/account/account-position-risk'
ACCOUNT_INFO = '/api/v5/account/balance'
POSITION_INFO = '/api/v5/account/positions'
BILLS_DETAIL = '/api/v5/account/bills'
BILLS_ARCHIVE = '/api/v5/account/bills-archive'
ACCOUNT_CONFIG = '/api/v5/account/config'
POSITION_MODE = '/api/v5/account/set-position-mode'
SET_LEVERAGE = '/api/v5/account/set-leverage'
MAX_TRADE_SIZE = '/api/v5/account/max-size'
MAX_AVAIL_SIZE = '/api/v5/account/max-avail-size'
ADJUSTMENT_MARGIN = '/api/v5/account/position/margin-balance'
GET_LEVERAGE = '/api/v5/account/leverage-info'
MAX_LOAN = '/api/v5/account/max-loan'
FEE_RATES = '/api/v5/account/trade-fee'
INTEREST_ACCRUED = '/api/v5/account/interest-accrued'
INTEREST_RATE = '/api/v5/account/interest-rate'
SET_GREEKS = '/api/v5/account/set-greeks'
ISOLATED_MODE = '/api/v5/account/set-isolated-mode'
MAX_WITHDRAWAL = '/api/v5/account/max-withdrawal'
ACCOUNT_RISK = '/api/v5/account/risk-state'
BORROW_REPAY = '/api/v5/account/borrow-repay'
BORROW_REPAY_HISTORY = '/api/v5/account/borrow-repay-history'
INTEREST_LIMITS = '/api/v5/account/interest-limits'
SIMULATED_MARGIN = '/api/v5/account/simulated_margin'
GREEKS = '/api/v5/account/greeks'

# funding
DEPOSIT_ADDRESS = '/api/v5/asset/deposit-address'
GET_BALANCES = '/api/v5/asset/balances'
FUNDS_TRANSFER = '/api/v5/asset/transfer'
TRANSFER_STATE = '/api/v5/asset/transfer-state'
WITHDRAWAL_COIN = '/api/v5/asset/withdrawal'
DEPOSIT_HISTORIY = '/api/v5/asset/deposit-history'
WITHDRAWAL_HISTORIY = '/api/v5/asset/withdrawal-history'
CURRENCY_INFO = '/api/v5/asset/currencies'
PURCHASE_REDEMPT = '/api/v5/asset/purchase_redempt'
BILLS_INFO = '/api/v5/asset/bills'
PIGGY_BALANCE = '/api/v5/asset/piggy-balance'
DEPOSIT_LIGHTNING = '/api/v5/asset/deposit-lightning'
WITHDRAWAL_LIGHTNING = '/api/v5/asset/withdrawal-lightning'
ASSET_VALUATION = '/api/v5/asset/asset-valuation'
SET_LENDING_RATE = '/api/v5/asset/set-lending-rate'
LENDING_HISTORY = '/api/v5/asset/lending-history'
LENDING_RATE_HISTORY = '/api/v5/asset/lending-rate-history'
LENDING_RATE_SUMMARY = '/api/v5/asset/lending-rate-summary'

# Market Data
TICKERS_INFO = '/api/v5/market/tickers'
TICKER_INFO = '/api/v5/market/ticker'
INDEX_TICKERS = '/api/v5/market/index-tickers'
ORDER_BOOKS = '/api/v5/market/books'
MARKET_CANDLES = '/api/v5/market/candles'
HISTORY_CANDLES = '/api/v5/market/history-candles'
INDEX_CANSLES = '/api/v5/market/index-candles'
MARKPRICE_CANDLES = '/api/v5/market/mark-price-candles'
MARKET_TRADES = '/api/v5/market/trades'
VOLUMNE = '/api/v5/market/platform-24-volume'
ORACLE = '/api/v5/market/oracle'
Components = '/api/v5/market/index-components'
EXCHANGE_RATE = '/api/v5/market/exchange-rate'

# Public Data
INSTRUMENT_INFO = '/api/v5/public/instruments'
DELIVERY_EXERCISE = '/api/v5/public/delivery-exercise-history'
OPEN_INTEREST = '/api/v5/public/open-interest'
FUNDING_RATE = '/api/v5/public/funding-rate'
FUNDING_RATE_HISTORY = '/api/v5/public/funding-rate-history'
PRICE_LIMIT = '/api/v5/public/price-limit'
OPT_SUMMARY = '/api/v5/public/opt-summary'
ESTIMATED_PRICE = '/api/v5/public/estimated-price'
DICCOUNT_INTETEST_INFO = '/api/v5/public/discount-rate-interest-free-quota'
SYSTEM_TIME = '/api/v5/public/time'
LIQUIDATION_ORDERS = '/api/v5/public/liquidation-orders'
MARK_PRICE = '/api/v5/public/mark-price'
TIER = '/api/v5/public/position-tiers'
INTEREST_LOAN = '/api/v5/public/interest-rate-loan-quota'
UNDERLYING = '/api/v5/public/underlying'
VIP_INTEREST_RATE_LOAN_QUOTA = '/api/v5/public/vip-interest-rate-loan-quota'

# TRADING DATA
SUPPORT_COIN = '/api/v5/rubik/stat/trading-data/support-coin'
TAKER_VOLUME = '/api/v5/rubik/stat/taker-volume'
MARGIN_LENDING_RATIO = '/api/v5/rubik/stat/margin/loan-ratio'
LONG_SHORT_RATIO = '/api/v5/rubik/stat/contracts/long-short-account-ratio'
CONTRACTS_INTEREST_VOLUME = '/api/v5/rubik/stat/contracts/open-interest-volume'
OPTIONS_INTEREST_VOLUME = '/api/v5/rubik/stat/option/open-interest-volume'
PUT_CALL_RATIO = '/api/v5/rubik/stat/option/open-interest-volume-ratio'
OPEN_INTEREST_VOLUME_EXPIRY = '/api/v5/rubik/stat/option/open-interest-volume-expiry'
INTEREST_VOLUME_STRIKE = '/api/v5/rubik/stat/option/open-interest-volume-strike'
TAKER_FLOW = '/api/v5/rubik/stat/option/taker-block-volume'

# TRADE
PLACR_ORDER = '/api/v5/trade/order'
BATCH_ORDERS = '/api/v5/trade/batch-orders'
CANAEL_ORDER = '/api/v5/trade/cancel-order'
CANAEL_BATCH_ORDERS = '/api/v5/trade/cancel-batch-orders'
AMEND_ORDER = '/api/v5/trade/amend-order'
AMEND_BATCH_ORDER = '/api/v5/trade/amend-batch-orders'
CLOSE_POSITION = '/api/v5/trade/close-position'
ORDER_INFO = '/api/v5/trade/order'
ORDERS_PENDING = '/api/v5/trade/orders-pending'
ORDERS_HISTORY = '/api/v5/trade/orders-history'
ORDERS_HISTORY_ARCHIVE = '/api/v5/trade/orders-history-archive'
ORDER_FILLS = '/api/v5/trade/fills'
ORDERS_FILLS_HISTORY = '/api/v5/trade/fills-history'
PLACE_ALGO_ORDER = '/api/v5/trade/order-algo'
CANCEL_ALGOS = '/api/v5/trade/cancel-algos'
Cancel_Advance_Algos = '/api/v5/trade/cancel-advance-algos'
ORDERS_ALGO_OENDING = '/api/v5/trade/orders-algo-pending'
ORDERS_ALGO_HISTORY = '/api/v5/trade/orders-algo-history'

# SubAccount
BALANCE = '/api/v5/account/subaccount/balances'
BILLs = '/api/v5/asset/subaccount/bills'
DELETE = '/api/v5/users/subaccount/delete-apikey'
RESET = '/api/v5/users/subaccount/modify-apikey'
CREATE = '/api/v5/users/subaccount/apikey'
WATCH = '/api/v5/users/subaccount/apikey'
VIEW_LIST = '/api/v5/users/subaccount/list'
SUBACCOUNT_TRANSFER = '/api/v5/asset/subaccount/transfer'
ENTRUST_SUBACCOUNT_LIST = '/api/v5/users/entrust-subaccount-list'

# Broker
BROKER_INFO = '/api/v5/broker/nd/info'
CREATE_SUBACCOUNT = '/api/v5/broker/nd/create-subaccount'
DELETE_SUBACCOUNT = '/api/v5/broker/nd/delete-subaccount'
SUBACCOUNT_INFO = '/api/v5/broker/nd/subaccount-info'
SET_SUBACCOUNT_LEVEL = '/api/v5/broker/nd/set-subaccount-level'
SET_SUBACCOUNT_FEE_REAT = '/api/v5/broker/nd/set-subaccount-fee-rate'
SUBACCOUNT_DEPOSIT_ADDRESS = '/api/v5/asset/broker/nd/subaccount-deposit-address'
SUBACCOUNT_DEPOSIT_HISTORY = '/api/v5/asset/broker/nd/subaccount-deposit-history'
REBATE_DAILY = '/api/v5/broker/nd/rebate-daily'
# BROKER_INFO = '/api/v5/broker/nd/info' Broker 获取充值地址文档无法打开，预留位置

# Convert
GET_CURRENCIES = '/api/v5/asset/convert/currencies'
GET_CURRENCY_PAIR = '/api/v5/asset/convert/currency-pair'
ESTIMATE_QUOTE = '/api/v5/asset/convert/estimate-quote'
CONVERT_TRADE = '/api/v5/asset/convert/trade'
CONVERT_HISTORY = '/api/v5/asset/convert/history'

# status
STATUS = '/api/v5/system/status'


def sign(message, secretKey):
    mac = hmac.new(bytes(secretKey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)


def pre_hash(timestamp, method, request_path, body):
    return str(timestamp) + str.upper(method) + request_path + body


def get_header(api_key, sign_, timestamp, passphrase, flag):
    header = dict()
    header[CONTENT_TYPE] = APPLICATION_JSON
    header[OK_ACCESS_KEY] = api_key
    header[OK_ACCESS_SIGN] = sign_
    header[OK_ACCESS_TIMESTAMP] = str(timestamp)
    header[OK_ACCESS_PASSPHRASE] = passphrase
    header['x-simulated-trading'] = flag
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


class OkxAPIException(Exception):

    def __init__(self, response):
        print(response.text + ', ' + str(response.status_code))
        self.code = 0
        try:
            json_res = response.json()
        except ValueError:
            self.message = 'Invalid JSON error message from Okx: {}'.format(response.text)
        else:
            if "code" in json_res.keys() and "msg" in json_res.keys():
                self.code = json_res['code']
                self.message = json_res['msg']
            else:
                self.code = 'None'
                self.message = 'System error'

        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        return 'API Request Error(code=%s): %s' % (self.code, self.message)


class OkxRequestException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'OkxRequestException: %s' % self.message


class OkxParamsException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'OkxParamsException: %s' % self.message


class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.flag = flag

        self.api_url = 'https://www.okx.com'

    def _request(self, method, request_path, params):

        if method == GET:
            request_path = request_path + parse_params_to_str(params)
        # url
        url = self.api_url + request_path

        timestamp = get_timestamp()

        # sign & header
        if self.use_server_time:
            timestamp = self._get_timestamp()

        body = json.dumps(params) if method == POST else ""

        sign_ = sign(pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = get_header(self.API_KEY, sign_, timestamp, self.PASSPHRASE, self.flag)
        # header["Content-Type"] = 'application/json'
        # header["OK_ACCESS_KEY"] = '141b8c40-bad4-4f6a-98f0-fd5944a529b1'
        #header["x-simulated-trading"] = '1'
        # header["OK_ACCESS_SIGN"] = 'TLWvAznkX8GUequwuvAb/weIFpV5ZXKlcSGvcwGPbl8='
        # header["OK_ACCESS_TIMESTAMP"] = '2022-03-17T05:36:39.355Z'
        # header["OK_ACCESS_PASSPHRASE"] = '123456'

        # send request
        response = None

        print("url:", url)
        # print("headers:", header)
        print("body:", body)

        if method == GET:
            response = requests.get(url, headers=header)
        elif method == POST:
            response = requests.post(url, data=body, headers=header)

        # exception handle
        # print(response.headers)

        if not str(response.status_code).startswith('2'):
            raise OkxAPIException(response)

        return response.json()

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params):
        return self._request(method, request_path, params)

    def _get_timestamp(self):
        url = self.api_url + SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['ts']
        else:
            return ""


class MarketAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, flag)

    # Get Tickers
    def get_tickers(self, instType, uly=''):
        if uly:
            params = {'instType': instType, 'uly': uly}
        else:
            params = {'instType': instType}
        return self._request_with_params(GET, TICKERS_INFO, params)

    # Get Ticker
    def get_ticker(self, instId):
        params = {'instId': instId}
        return self._request_with_params(GET, TICKER_INFO, params)

    # Get Index Tickers
    def get_index_ticker(self, quoteCcy='', instId=''):
        params = {'quoteCcy': quoteCcy, 'instId': instId}
        return self._request_with_params(GET, INDEX_TICKERS, params)

    # Get Order Book
    def get_orderbook(self, instId, sz=''):
        params = {'instId': instId, 'sz': sz}
        return self._request_with_params(GET, ORDER_BOOKS, params)

    # Get Candlesticks
    def get_candlesticks(self, instId, after='', before='', bar='', limit=''):
        params = {'instId': instId, 'after': after, 'before': before, 'bar': bar, 'limit': limit}
        return self._request_with_params(GET, MARKET_CANDLES, params)

    # GGet Candlesticks History（top currencies only）
    def get_history_candlesticks(self, instId, after='', before='', bar='', limit=''):
        params = {'instId': instId, 'after': after, 'before': before, 'bar': bar, 'limit': limit}
        return self._request_with_params(GET, HISTORY_CANDLES, params)

    # Get Index Candlesticks
    def get_index_candlesticks(self, instId, after='', before='', bar='', limit=''):
        params = {'instId': instId, 'after': after, 'before': before, 'bar': bar, 'limit': limit}
        return self._request_with_params(GET, INDEX_CANSLES, params)

    # Get Mark Price Candlesticks
    def get_markprice_candlesticks(self, instId, after='', before='', bar='', limit=''):
        params = {'instId': instId, 'after': after, 'before': before, 'bar': bar, 'limit': limit}
        return self._request_with_params(GET, MARKPRICE_CANDLES, params)

    # Get Index Candlesticks
    def get_trades(self, instId, limit=''):
        params = {'instId': instId, 'limit': limit}
        return self._request_with_params(GET, MARKET_TRADES, params)

    # Get Volume
    def get_volume(self):
        return self._request_without_params(GET, VOLUMNE)

    # Get Oracle
    def get_oracle(self):
        return self._request_without_params(GET, ORACLE)

    # Get Index Components
    def get_index_components(self, index):
        params = {'index': index}
        return self._request_with_params(GET, Components, params)

    # Get Tier
    def get_tier(self, instType='', tdMode='', uly='', instId='', ccy='', tier=''):
        params = {'instType': instType, 'tdMode': tdMode, 'uly': uly, 'instId': instId, 'ccy': ccy, 'tier': tier}
        return self._request_with_params(GET, TIER, params)

    # Get exchange rate
    def get_exchange_rate(self):
        params = {}
        return self._request_with_params(GET, BORROW_REPAY, params)


class TradeAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, flag)

    # Place Order
    def place_order(self, instId, tdMode, side, ordType, sz, ccy='', clOrdId='', tag='', posSide='', px='',
                    reduceOnly='', tgtCcy=''):
        params = {'instId': instId, 'tdMode': tdMode, 'side': side, 'ordType': ordType, 'sz': sz, 'ccy': ccy,
                  'clOrdId': clOrdId, 'tag': tag, 'posSide': posSide, 'px': px, 'reduceOnly': reduceOnly,
                  'tgtCcy': tgtCcy}
        return self._request_with_params(POST, PLACR_ORDER, params)

    # Place Multiple Orders
    def place_multiple_orders(self, orders_data):
        return self._request_with_params(POST, BATCH_ORDERS, orders_data)

    # Cancel Order
    def cancel_order(self, instId, ordId='', clOrdId=''):
        params = {'instId': instId, 'ordId': ordId, 'clOrdId': clOrdId}
        return self._request_with_params(POST, CANAEL_ORDER, params)

    # Cancel Multiple Orders
    def cancel_multiple_orders(self, orders_data):
        return self._request_with_params(POST, CANAEL_BATCH_ORDERS, orders_data)

    # Amend Order
    def amend_order(self, instId, cxlOnFail='', ordId='', clOrdId='', reqId='', newSz='', newPx=''):
        params = {'instId': instId, 'cxlOnFailc': cxlOnFail, 'ordId': ordId, 'clOrdId': clOrdId, 'reqId': reqId,
                  'newSz': newSz,
                  'newPx': newPx}
        return self._request_with_params(POST, AMEND_ORDER, params)

    # Amend Multiple Orders
    def amend_multiple_orders(self, orders_data):
        return self._request_with_params(POST, AMEND_BATCH_ORDER, orders_data)

    # Close Positions
    def close_positions(self, instId, mgnMode, posSide='', ccy='', autoCxl=''):
        params = {'instId': instId, 'mgnMode': mgnMode, 'posSide': posSide, 'ccy': ccy, 'autoCxl': autoCxl}
        return self._request_with_params(POST, CLOSE_POSITION, params)

    # Get Order Details
    def get_orders(self, instId, ordId='', clOrdId=''):
        params = {'instId': instId, 'ordId': ordId, 'clOrdId': clOrdId}
        return self._request_with_params(GET, ORDER_INFO, params)

    # Get Order List
    def get_order_list(self, instType='', uly='', instId='', ordType='', state='', after='', before='', limit=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId, 'ordType': ordType, 'state': state,
                  'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, ORDERS_PENDING, params)

    # Get Order History (last 7 days）
    def get_orders_history(self, instType, uly='', instId='', ordType='', state='', after='', before='', limit=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId, 'ordType': ordType, 'state': state,
                  'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, ORDERS_HISTORY, params)

    # Get Order History (last 3 months)
    def orders_history_archive(self, instType, uly='', instId='', ordType='', state='', after='', before='', limit=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId, 'ordType': ordType, 'state': state,
                  'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, ORDERS_HISTORY_ARCHIVE, params)

    # Get Transaction Details
    def get_fills(self, instType='', uly='', instId='', ordId='', after='', before='', limit=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId, 'ordId': ordId, 'after': after, 'before': before,
                  'limit': limit}
        return self._request_with_params(GET, ORDER_FILLS, params)

    # Place Algo Order
    def place_algo_order(self, instId='', tdMode='', side='', ordType='', sz='', ccy='',
                         posSide='', reduceOnly='', tpTriggerPx='',
                         tpOrdPx='', slTriggerPx='', slOrdPx='',
                         triggerPx='', orderPx='', tgtCcy='', pxVar='',
                         pxSpread='',
                         szLimit='', pxLimit='', timeInterval='', tpTriggerPxType='', slTriggerPxType='',
                         callbackRatio='', callbackSpread='', activePx='', tag='', triggerPxType=''):
        params = {'instId': instId, 'tdMode': tdMode, 'side': side, 'ordType': ordType, 'sz': sz, 'ccy': ccy,
                  'posSide': posSide, 'reduceOnly': reduceOnly, 'tpTriggerPx': tpTriggerPx, 'tpOrdPx': tpOrdPx,
                  'slTriggerPx': slTriggerPx, 'slOrdPx': slOrdPx, 'triggerPx': triggerPx, 'orderPx': orderPx,
                  'tgtCcy': tgtCcy, 'pxVar': pxVar, 'szLimit': szLimit, 'pxLimit': pxLimit,
                  'timeInterval': timeInterval,
                  'pxSpread': pxSpread, 'tpTriggerPxType': tpTriggerPxType, 'slTriggerPxType': slTriggerPxType,
                  'callbackRatio': callbackRatio, 'callbackSpread': callbackSpread, 'activePx': activePx,
                  'tag': tag, 'triggerPxType': triggerPxType, }
        return self._request_with_params(POST, PLACE_ALGO_ORDER, params)

    # Cancel Algo Order
    def cancel_algo_order(self, params):
        return self._request_with_params(POST, CANCEL_ALGOS, params)

    # Cancel Advance Algos
    def cancel_advance_algos(self, params):
        return self._request_with_params(POST, Cancel_Advance_Algos, params)

    # Get Algo Order List
    def order_algos_list(self, ordType, algoId='', instType='', instId='', after='', before='', limit=''):
        params = {'ordType': ordType, 'algoId': algoId, 'instType': instType, 'instId': instId, 'after': after,
                  'before': before, 'limit': limit}
        return self._request_with_params(GET, ORDERS_ALGO_OENDING, params)

    # Get Algo Order History
    def order_algos_history(self, ordType, state='', algoId='', instType='', instId='', after='', before='', limit=''):
        params = {'ordType': ordType, 'state': state, 'algoId': algoId, 'instType': instType, 'instId': instId,
                  'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, ORDERS_ALGO_HISTORY, params)

    # Get Transaction Details History
    def get_fills_history(self, instType, uly='', instId='', ordId='', after='', before='', limit=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId, 'ordId': ordId, 'after': after, 'before': before,
                  'limit': limit}
        return self._request_with_params(GET, ORDERS_FILLS_HISTORY, params)


class ConvertAPI(Client):
    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, flag)

    def get_currencies(self):
        params = {}
        return self._request_with_params(GET, GET_CURRENCIES, params)

    def get_currency_pair(self, fromCcy='', toCcy=''):
        params = {"fromCcy": fromCcy, 'toCcy': toCcy}
        return self._request_with_params(GET, GET_CURRENCY_PAIR, params)

    def estimate_quote(self, baseCcy='', quoteCcy='', side='', rfqSz='', rfqSzCcy='', clQReqId=''):
        params = {'baseCcy': baseCcy, 'quoteCcy': quoteCcy, 'side': side, 'rfqSz': rfqSz, 'rfqSzCcy': rfqSzCcy,
                  'clQReqId': clQReqId}
        return self._request_with_params(POST, ESTIMATE_QUOTE, params)

    def convert_trade(self, quoteId='', baseCcy='', quoteCcy='', side='', sz='', szCcy='', clTReqId=''):
        params = {'quoteId': quoteId, 'baseCcy': baseCcy, 'quoteCcy': quoteCcy, 'side': side, 'sz': sz, 'szCcy': szCcy,
                  'clTReqId': clTReqId}
        return self._request_with_params(POST, CONVERT_TRADE, params)

    def get_convert_history(self, after='', before='', limit=''):
        params = {'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, CONVERT_HISTORY, params)


class AccountAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, flag)

    # Get Positions
    def get_position_risk(self, instType=''):
        params = {}
        if instType:
            params['instType'] = instType
        return self._request_with_params(GET, POSITION_RISK, params)

    # Get Balance
    def get_account(self, ccy=''):
        params = {}
        if ccy:
            params['ccy'] = ccy
        return self._request_with_params(GET, ACCOUNT_INFO, params)

    # Get Positions
    def get_positions(self, instType='', instId=''):
        params = {'instType': instType, 'instId': instId}
        return self._request_with_params(GET, POSITION_INFO, params)

    # Get Bills Details (recent 7 days)
    def get_bills_detail(self, instType='', ccy='', mgnMode='', ctType='', type='', subType='', after='', before='',
                         limit=''):
        params = {'instType': instType, 'ccy': ccy, 'mgnMode': mgnMode, 'ctType': ctType, 'type': type,
                  'subType': subType, 'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, BILLS_DETAIL, params)

    # Get Bills Details (recent 3 months)
    def get_bills_details(self, instType='', ccy='', mgnMode='', ctType='', type='', subType='', after='', before='',
                          limit=''):
        params = {'instType': instType, 'ccy': ccy, 'mgnMode': mgnMode, 'ctType': ctType, 'type': type,
                  'subType': subType, 'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, BILLS_ARCHIVE, params)

    # Get Account Configuration
    def get_account_config(self):
        return self._request_without_params(GET, ACCOUNT_CONFIG)

    # Get Account Configuration
    def get_position_mode(self, posMode):
        params = {'posMode': posMode}
        return self._request_with_params(POST, POSITION_MODE, params)

    # Get Account Configuration
    def set_leverage(self, lever, mgnMode, instId='', ccy='', posSide=''):
        params = {'lever': lever, 'mgnMode': mgnMode, 'instId': instId, 'ccy': ccy, 'posSide': posSide}
        return self._request_with_params(POST, SET_LEVERAGE, params)

    # Get Maximum Tradable Size For Instrument
    def get_maximum_trade_size(self, instId, tdMode, ccy='', px='', leverage=''):
        params = {'instId': instId, 'tdMode': tdMode, 'ccy': ccy, 'px': px, 'leverage': leverage}
        return self._request_with_params(GET, MAX_TRADE_SIZE, params)

    # Get Maximum Available Tradable Amount
    def get_max_avail_size(self, instId, tdMode, ccy='', reduceOnly=''):
        params = {'instId': instId, 'tdMode': tdMode, 'ccy': ccy, 'reduceOnly': reduceOnly}
        return self._request_with_params(GET, MAX_AVAIL_SIZE, params)

    # Increase / Decrease margin
    def Adjustment_margin(self, instId, posSide, type, amt, loanTrans=''):
        params = {'instId': instId, 'posSide': posSide, 'type': type, 'amt': amt, 'loanTrans': loanTrans}
        return self._request_with_params(POST, ADJUSTMENT_MARGIN, params)

    # Get Leverage
    def get_leverage(self, instId, mgnMode):
        params = {'instId': instId, 'mgnMode': mgnMode}
        return self._request_with_params(GET, GET_LEVERAGE, params)

    # Get the maximum loan of isolated MARGIN
    def get_max_load(self, instId, mgnMode, mgnCcy):
        params = {'instId': instId, 'mgnMode': mgnMode, 'mgnCcy': mgnCcy}
        return self._request_with_params(GET, MAX_LOAN, params)

    # Get Fee Rates
    def get_fee_rates(self, instType, instId='', uly='', category=''):
        params = {'instType': instType, 'instId': instId, 'uly': uly, 'category': category}
        return self._request_with_params(GET, FEE_RATES, params)

    # Get interest-accrued
    def get_interest_accrued(self, instId='', ccy='', mgnMode='', after='', before='', limit='', type=''):
        params = {'instId': instId, 'ccy': ccy, 'mgnMode': mgnMode, 'after': after, 'before': before, 'limit': limit,
                  'type': type}
        return self._request_with_params(GET, INTEREST_ACCRUED, params)

    # Get interest-accrued
    def get_interest_rate(self, ccy=''):
        params = {'ccy': ccy}
        return self._request_with_params(GET, INTEREST_RATE, params)

    # Set Greeks (PA/BS)
    def set_greeks(self, greeksType):
        params = {'greeksType': greeksType}
        return self._request_with_params(POST, SET_GREEKS, params)

    # Set Isolated Mode
    def set_isolated_mode(self, isoMode, type):
        params = {'isoMode': isoMode, 'type': type}
        return self._request_with_params(POST, ISOLATED_MODE, params)

    # Get Maximum Withdrawals
    def get_max_withdrawal(self, ccy=''):
        params = {'ccy': ccy}
        return self._request_with_params(GET, MAX_WITHDRAWAL, params)

    # Get account risk state
    def get_account_risk(self):
        return self._request_without_params(GET, ACCOUNT_RISK)

    # Get borrow repay
    def borrow_repay(self, ccy='', side='', amt=''):
        params = {'ccy': ccy, 'side': side, 'amt': amt}
        return self._request_with_params(POST, BORROW_REPAY, params)

    # Get borrow repay history
    def get_borrow_repay_history(self, ccy='', after='', before='', limit=''):
        params = {'ccy': ccy, 'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, BORROW_REPAY_HISTORY, params)

    # Get Obtain borrowing rate and limit
    def get_interest_limits(self, type='', ccy=''):
        params = {'type': type, 'ccy': ccy}
        return self._request_with_params(GET, INTEREST_LIMITS, params)

    # Get Simulated Margin
    def get_simulated_margin(self, instType='', inclRealPos='', instId='', pos=''):
        params = {'instType': instType, 'inclRealPos': inclRealPos, 'instId': instId, 'pos': pos, }
        return self._request_with_params(GET, SIMULATED_MARGIN, params)

    # Get  Greeks
    def get_greeks(self, ccy=''):
        params = {'ccy': ccy, }
        return self._request_with_params(GET, GREEKS, params)

class FundingAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, flag)

    # Get Deposit Address
    def get_deposit_address(self, ccy):
        params = {'ccy': ccy}
        return self._request_with_params(GET, DEPOSIT_ADDRESS, params)

    # Get Balance
    def get_balances(self, ccy=''):
        params = {'ccy': ccy}
        return self._request_with_params(GET, GET_BALANCES, params)

    # POST Account Configuration
    def funds_transfer(self, ccy, amt, froms, to, type='0', subAcct='', instId='', toInstId='',loanTrans=''):
        params = {'ccy': ccy, 'amt': amt, 'from': froms, 'to': to, 'type': type, 'subAcct': subAcct, 'instId': instId,
                  'toInstId': toInstId,'loanTrans':loanTrans}
        return self._request_with_params(POST, FUNDS_TRANSFER, params)

    # Get Transfer State
    def transfer_state(self, transId,type=''):
        params = {'transId': transId, 'type': type}
        return self._request_with_params(POST, TRANSFER_STATE, params)

    # Withdrawal
    def coin_withdraw(self, ccy, amt, dest, toAddr, pwd, fee,chain=''):
        params = {'ccy': ccy, 'amt': amt, 'dest': dest, 'toAddr': toAddr, 'pwd': pwd, 'fee': fee,'chain': chain}
        return self._request_with_params(POST, WITHDRAWAL_COIN, params)

    # Get Deposit History
    def get_deposit_history(self, ccy='', state='', after='', before='', limit='',txId=''):
        params = {'ccy': ccy, 'state': state, 'after': after, 'before': before, 'limit': limit,'txId':txId}
        return self._request_with_params(GET, DEPOSIT_HISTORIY, params)

    # Get Withdrawal History
    def get_withdrawal_history(self, ccy='', state='', after='', before='', limit='',txId=''):
        params = {'ccy': ccy, 'state': state, 'after': after, 'before': before, 'limit': limit,'txId':txId}
        return self._request_with_params(GET, WITHDRAWAL_HISTORIY, params)

    # Get Currencies
    def get_currency(self):
        return self._request_without_params(GET, CURRENCY_INFO)

    # PiggyBank Purchase/Redemption
    def purchase_redempt(self, ccy, amt, side,rate):
        params = {'ccy': ccy, 'amt': amt, 'side': side,'rate': rate}
        return self._request_with_params(POST, PURCHASE_REDEMPT, params)

    # Get Withdrawal History
    def get_bills(self, ccy='', type='', after='', before='', limit=''):
        params = {'ccy': ccy, 'type': type, 'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, BILLS_INFO, params)


    #Get Piggy Balance
    def get_piggy_balance(self, ccy=''):
        params = {}
        if ccy:
            params = {'ccy':ccy}
        return self._request_with_params(GET, PIGGY_BALANCE, params)


    #Get Deposit Lightning
    def get_deposit_lightning(self, ccy,amt,to=""):
        params = {'ccy':ccy,'amt':amt}
        if to:
            params = {'to':to}
        return self._request_with_params(GET, DEPOSIT_LIGHTNING, params)

    # Withdrawal Lightning
    def withdrawal_lightning(self, ccy,invoice,pwd):
        params = {'ccy':ccy, 'invoice':invoice, 'pwd':pwd}
        return self._request_with_params(POST, WITHDRAWAL_LIGHTNING, params)


    # GET Obtain account asset valuation
    def get_asset_valuation(self, ccy):
        params = {'ccy':ccy}
        return self._request_with_params(GET, ASSET_VALUATION, params)

    # POST SET LENDING RATE
    def set_lending_rate(self, ccy,rate):
        params = {'ccy':ccy,'rate':rate}
        return self._request_with_params(POST, SET_LENDING_RATE, params)


    # GET LENDING HISTORY
    def get_lending_rate(self, ccy='',before='',after='',limit='',):
        params = {'ccy': ccy, 'after': after, 'before': before, 'limit': limit,}
        return self._request_with_params(GET, LENDING_HISTORY, params)


    # GET LENDING RATE HISTORY
    def get_lending_rate_history(self, ccy='',):
        params = {'ccy': ccy,}
        return self._request_with_params(GET, LENDING_RATE_HISTORY, params)

    # GET LENDING RATE SUMMARY
    def get_lending_rate_summary(self, ccy='',before='',after='',limit='',):
        params = {'ccy': ccy, 'after': after, 'before': before, 'limit': limit,}
        return self._request_with_params(GET,LENDING_RATE_SUMMARY, params)

class PublicAPI(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1'):
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, flag)

    # Get Instruments
    def get_instruments(self, instType, uly='', instId=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId}
        return self._request_with_params(GET, INSTRUMENT_INFO, params)

    # Get Delivery/Exercise History
    def get_deliver_history(self, instType, uly, after='', before='', limit=''):
        params = {'instType': instType, 'uly': uly, 'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, DELIVERY_EXERCISE, params)

    # Get Open Interest
    def get_open_interest(self, instType, uly='', instId=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId}
        return self._request_with_params(GET, OPEN_INTEREST, params)

    # Get Funding Rate
    def get_funding_rate(self, instId):
        params = {'instId': instId}
        return self._request_with_params(GET, FUNDING_RATE, params)

    # Get Funding Rate History
    def funding_rate_history(self, instId, after='', before='', limit=''):
        params = {'instId': instId, 'after': after, 'before': before, 'limit': limit}
        return self._request_with_params(GET, FUNDING_RATE_HISTORY, params)

    # Get Limit Price
    def get_price_limit(self, instId):
        params = {'instId': instId}
        return self._request_with_params(GET, PRICE_LIMIT, params)

    # Get Option Market Data
    def get_opt_summary(self, uly, expTime=''):
        params = {'uly': uly, 'expTime': expTime}
        return self._request_with_params(GET, OPT_SUMMARY, params)

    # Get Estimated Delivery/Excercise Price
    def get_estimated_price(self, instId):
        params = {'instId': instId}
        return self._request_with_params(GET, ESTIMATED_PRICE, params)

    # Get Discount Rate And Interest-Free Quota
    def discount_interest_free_quota(self, ccy=''):
        params = {'ccy': ccy}
        return self._request_with_params(GET, DICCOUNT_INTETEST_INFO, params)

    # Get System Time
    def get_system_time(self):
        return self._request_without_params(GET, SYSTEM_TIME)

    # Get Liquidation Orders
    def get_liquidation_orders(self, instType, mgnMode='', instId='', ccy='', uly='', alias='', state='', before='',
                               after='', limit=''):
        params = {'instType': instType, 'mgnMode': mgnMode, 'instId': instId, 'ccy': ccy, 'uly': uly,
                  'alias': alias, 'state': state, 'before': before, 'after': after, 'limit': limit}
        return self._request_with_params(GET, LIQUIDATION_ORDERS, params)

    # Get Mark Price
    def get_mark_price(self, instType, uly='', instId=''):
        params = {'instType': instType, 'uly': uly, 'instId': instId}
        return self._request_with_params(GET, MARK_PRICE, params)

    # Get Tier
    def get_tier(self, instType, tdMode, uly='', instId='', ccy='', tier=''):
        params = {'instType': instType, 'tdMode': tdMode, 'uly': uly, 'instId': instId, 'ccy': ccy, 'tier': tier}
        return self._request_with_params(GET, TIER, params)

    # Get Interest Rate and Loan Quota
    def get_interest_loan(self):
        return self._request_without_params(GET, INTEREST_LOAN)

    # Get underlying

    def get_underlying(self, instType):
        params = {'instType': instType}
        return self._request_with_params(GET, UNDERLYING, params)

    # GET Obtain the privileged currency borrowing leverage rate and currency borrowing limit
    def get_vip_interest_rate_loan_quota(self):
        params = {}
        return self._request_with_params(GET, VIP_INTEREST_RATE_LOAN_QUOTA, params)