"""
    Functions for managing Exchange API Keys
    Copyright (C) 2022 Matias Kotlik

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

import alpaca_trade_api
from binance.client import Client as BinanceClient

from blankly.deployment.exchange_data import Exchange
from blankly.deployment.ui import print_failure, show_spinner
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI

from blankly.deployment.ui import confirm


def load_keys():
    try:
        with open('keys.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def write_keys(data):
    with open('keys.json', 'w') as file:
        json.dump(data, file, indent=4)


def add_key(exchange: Exchange, tld: str, key_name: str, data: dict):
    # load old keys file
    saved_data = load_keys()

    keys = saved_data.setdefault(exchange.name, {})

    # change name until it's not already in our file
    if not key_name:
        key_name = 'example-portfolio'
    if key_name in keys:
        key_name = key_name + '-1'
    while key_name in keys:
        base, num = key_name.rsplit('-', 1)
        key_name = f'{base}-{int(num) + 1}'

    keys[key_name] = data  # this writes to saved_data

    key_is_valid = check_key(exchange, tld, data)
    if key_is_valid or confirm('Would you like to save this key anyway?', default=False).unsafe_ask():
        write_keys(saved_data)
        return True
    return False


def check_key(exchange: Exchange, tld: str, auth):
    with show_spinner(f'Checking {exchange.display_name} API Key') as spinner:
        try:
            exchange.test_func(auth, tld)
        except Exception:
            spinner.fail(f'Failed to connect to {exchange.display_name}. Check that your keys are valid.')
            return False
        spinner.ok(f'Checked {exchange.display_name} API Key')
        return True
