import json

import alpaca_trade_api
from binance.client import Client as BinanceClient

from blankly.deployment.ui import print_failure, show_spinner
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI

from blankly.deployment.ui import confirm


def split_exchange(exchange):
    if '.' in exchange:
        return exchange.rsplit('.')
    return exchange, None


def add_key(exchange: str, tld: str, name: str, data: dict):
    # load old keys file
    try:
        with open('keys.json', 'r') as file:
            saved_data = json.load(file)
    except FileNotFoundError:
        saved_data = {}

    keys = saved_data.setdefault(exchange, {})

    # change name until it's not already in our file
    if not name:
        name = 'default'
    if name in keys:
        name = name + '-1'
    while name in keys:
        base, num = name.rsplit('-')
        name = f'{base}-{int(num) + 1}'

    keys[name] = data  # this writes to saved_data

    key_is_valid = check_key(exchange, tld, data)
    if confirm('Would you like to save this key anyway?', default=False) \
            .skip_if(key_is_valid, True).ask():
        with open('keys.json', 'w') as file:
            json.dump(saved_data, file, indent=4)
        return True
    return False


def check_key(exchange, tld, data):
    test_func = get_test_func(exchange, tld, data)
    if not test_func:
        print_failure(f'Blankly can\'t check {exchange} API Keys at this time')
        return True

    with show_spinner(f'Checking {exchange} API Key') as spinner:
        try:
            test_func()
        except Exception:
            spinner.fail(f'Failed to connect to {exchange}. Check that your keys are valid.')
            return False
        spinner.ok(f'Checked {exchange} API Key')
        return True


def get_test_func(exchange, tld, data):
    if exchange == 'binance':
        return BinanceClient(api_key=data['API_KEY'], api_secret=data['API_SECRET'], tld=tld).get_account
    elif exchange == 'coinbase_pro':
        return CoinbaseProAPI(api_key=data['API_KEY'], api_secret=data['API_SECRET'],
                              api_pass=data['API_PASS']).get_account
    elif exchange == 'alpaca':
        return alpaca_trade_api.REST(key_id=data['API_KEY'], secret_key=data['API_SECRET']).get_account
    elif exchange == 'oanda':
        return OandaAPI(personal_access_token=data['PERSONAL_ACCESS_TOKEN'],
                        account_id=data['ACCOUNT_ID']).get_account
    elif exchange == 'ftx':
        return FTXAPI(data['API_KEY'], data['API_SECRET'], tld).get_account_info
    elif exchange == 'kucoin':
        try:
            from kucoin import client as KucoinAPI
        except ImportError:
            print_failure('kucoin-python must be installed to check Kucoin API Keys')
            return
        return KucoinAPI.User(data['API_KEY'], data['API_SECRET'], data['API_PASS']).get_base_fee
