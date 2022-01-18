"""
    Kucoin interface definition
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


class Kucoin(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "kucoin", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'kucoin', ['API_KEY', 'API_SECRET', 'API_PASS'])

        sandbox = self.preferences["settings"]["use_sandbox"]
        try:
            from kucoin import client as KucoinAPI
        except ImportError:
            raise ImportError("Please \"pip install kucoin-python\" to use kucoin with blankly.")
        # Kucoin has a bunch of calls types, so we will index them in a single calls dictionary
        calls = {
            'market': KucoinAPI.Market(auth.keys['API_KEY'], auth.keys['API_SECRET'], auth.keys['API_PASS'], sandbox),
            'user': KucoinAPI.User(auth.keys['API_KEY'], auth.keys['API_SECRET'], auth.keys['API_PASS'], sandbox),
            'trade': KucoinAPI.Trade(auth.keys['API_KEY'], auth.keys['API_SECRET'], auth.keys['API_PASS'], sandbox)
        }

        # Always finish the method with this function
        super().construct_interface_and_cache(calls)

    """
    Builds information about the asset on this exchange by making particular API calls
    """

    def get_asset_state(self, symbol):
        """
        This determines the internal properties of the exchange block.
        Should be implemented per-class because it requires different types of interaction with each exchange.
        """
        # TODO Populate this with useful information
        return self.interface.get_account(symbol)

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.interface.get_fees()

    def get_direct_calls(self) -> dict:
        return self.calls

