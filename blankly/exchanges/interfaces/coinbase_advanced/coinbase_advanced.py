"""
    Coinbase Advanced exchange definitions and setup
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

from blankly.exchanges.exchange import Exchange
from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI


class CoinbaseAdvanced(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "coinbase_advanced", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'coinbase_advanced', ['API_KEY', 'API_SECRET', 'API_PASS',
                                                                                 'sandbox'])

        sandbox = super().evaluate_sandbox(auth)

        keys = auth.keys

        if sandbox:
            calls = CoinbaseProAPI(api_key=keys['API_KEY'],
                                   api_secret=keys['API_SECRET'],
                                   api_url="https://api-public.sandbox.pro.coinbase.com/")
        else:
            calls = CoinbaseProAPI(api_key=keys['API_KEY'],
                                   api_secret=keys['API_SECRET'],
                                   api_url="https://api.exchange.coinbase.com")


        # Always finish the method with this function
        super().construct_interface_and_cache(calls)

    def get_asset_state(self, symbol):
        return self.interface.get_account(symbol)

    def get_direct_calls(self) -> CoinbaseProAPI:
        return self.calls