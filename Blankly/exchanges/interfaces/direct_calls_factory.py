"""
    Final constructor for authentication objects
    Copyright (C) 2021  Arun Annamalai, Emerson Dove

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


from Blankly.exchanges.auth.abc_auth import ABCAuth
from Blankly.exchanges.interfaces.alpaca.alpaca_interface import AlpacaInterface
from Blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as Coinbase_Pro_API
from binance.client import Client
from Blankly.exchanges.interfaces.alpaca.alpaca_api import create_alpaca_client
from Blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_interface import CoinbaseProInterface
from Blankly.exchanges.interfaces.binance.binance_interface import BinanceInterface
import Blankly.utils.utils as utils


class DirectCallsFactory:
    @staticmethod
    def create(exchange_name: str, auth: ABCAuth, preferences_path: str = None):
        preferences = utils.load_user_preferences(preferences_path)
        if exchange_name == 'coinbase_pro':
            if preferences["settings"]["use_sandbox"]:
                calls = Coinbase_Pro_API(auth, API_URL="https://api-public.sandbox.pro.coinbase.com/")
            else:
                # Create the authenticated object
                calls = Coinbase_Pro_API(auth)

            return calls, CoinbaseProInterface(exchange_name, calls)

        elif exchange_name == 'binance':
            if preferences["settings"]["use_sandbox"] or preferences["settings"]["paper_trade"]:
                calls = Client(api_key=auth.keys['API_KEY'], api_secret=auth.keys['API_SECRET'],
                               tld=preferences["settings"]['binance']["binance_tld"],
                               testnet=True)
            else:
                calls = Client(api_key=auth.keys['API_KEY'], api_secret=auth.keys['API_SECRET'],
                               tld=preferences["settings"]['binance']["binance_tld"])
            return calls, BinanceInterface(exchange_name, calls)

        elif exchange_name == 'alpaca':
            calls = create_alpaca_client(auth, preferences["settings"]["use_sandbox"])
            return calls, AlpacaInterface(calls, preferences_path)

        elif exchange_name == 'paper_trade':
            return None, None
