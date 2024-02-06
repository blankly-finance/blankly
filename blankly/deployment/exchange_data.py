"""
    Exchange metadata for use in the CLI
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

from typing import Dict, List
import alpaca_trade_api
from binance.client import Client as BinanceClient
from questionary import Choice

from blankly.deployment.ui import print_failure
from blankly.exchanges.interfaces.alpaca import alpaca_api
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI
from blankly.exchanges.interfaces.oanda.oanda_api import OandaAPI


class Exchange:
    name: str
    symbols: List[str]
    python_class: str
    tlds: List[str]
    display_name: str
    key_info: Dict[str, str]

    def __init__(self, name: str, symbols: List[str], test_func, key_info: List[str] = None, python_class: str = None,
                 tlds: List[str] = None, display_name: str = None, currency: str = 'USD'):
        self.name = name
        self.symbols = symbols
        self.test_func = test_func
        self.key_info = {k.replace('_', ' ').title().replace('Api', 'API'): k  # autogen key instructions
                         for k in key_info or ['API_KEY', 'API_SECRET']}  # default to just key/secret
        self.python_class = python_class or name.replace('_', ' ').title().replace(' ', '')  # snake case to pascalcase
        self.tlds = tlds or []
        self.display_name = display_name or name.replace('_', ' ').title()  # prettify
        self.currency = currency


def kucoin_test_func(auth, tld):
    try:
        from kucoin import client as KucoinAPI
    except ImportError:
        print()  # we are running loading bar at this point, go next line to avoid making a mess
        print_failure('kucoin-python must be installed to check Kucoin API Keys')
        print_failure('Skipping check')
    else:
        return KucoinAPI.User(auth['API_KEY'], auth['API_SECRET'], auth['API_PASS'], auth['sandbox']).get_base_fee


EXCHANGES = [
    Exchange('alpaca', ['MSFT', 'GME', 'AAPL'],
             lambda auth, tld: alpaca_trade_api.REST(key_id=auth['API_KEY'],
                                                     secret_key=auth['API_SECRET'],
                                                     base_url=(alpaca_api.live_url,
                                                               alpaca_api.paper_url)[auth['sandbox']]
                                                     ).get_account()),
    Exchange('binance', ['BTC-USDT', 'ETH-USDT', 'SOL-USDT'],
             lambda auth, tld: BinanceClient(api_key=auth['API_KEY'], api_secret=auth['API_SECRET'],
                                             tld=tld, testnet=auth['sandbox']).get_account(),
             tlds=['com', 'us'], currency='USDT'),
    Exchange('coinbase_pro', ['BTC-USD', 'ETH-USD', 'SOL-USD'],
             lambda auth, tld: CoinbaseProAPI(api_key=auth['API_KEY'], api_secret=auth['API_SECRET'],
                                              api_pass=auth['API_PASS'],
                                              API_URL=('https://api.pro.coinbase.com/',
                                                       'https://api-public.sandbox.pro.coinbase.com/')[auth['sandbox']]
                                              ).get_accounts(),
             key_info=['API_KEY', 'API_SECRET', 'API_PASS']),
    Exchange('ftx', ['BTC-USD', 'ETH-USD', 'SOL-USD'],
             lambda auth, tld: FTXAPI(auth['API_KEY'], auth['API_SECRET'], tld).get_account_info(),
             tlds=['com', 'us'], python_class='FTX', display_name='FTX'),
    Exchange('oanda', ['BTC-USD', 'ETH-USD', 'SOL-USD'],
             lambda auth, tld: OandaAPI(personal_access_token=auth['PERSONAL_ACCESS_TOKEN'],
                                        account_id=auth['ACCOUNT_ID'], sandbox=auth['sandbox']).get_account(),
             key_info=['ACCOUNT_ID', 'PERSONAL_ACCESS_TOKEN']),
    Exchange('kucoin', ['BTC-USDT', 'ETH-USDT', 'SOL-USDT'], kucoin_test_func,
             key_info=['API_KEY', 'API_SECRET', 'API_PASS'], currency='USDT'),
]

EXCHANGE_CHOICES_NO_KEYLESS = [Choice(exchange.display_name, exchange)
                               for exchange in EXCHANGES]
EXCHANGE_CHOICES = EXCHANGE_CHOICES_NO_KEYLESS[:]
EXCHANGE_CHOICES.append(Choice('Keyless/No Exchange', False))


def exc_display_name(name):
    return next((exchange.display_name for exchange in EXCHANGES if name == exchange.name), name)
