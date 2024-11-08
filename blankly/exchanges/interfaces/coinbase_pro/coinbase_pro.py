"""
    Coinbase Pro exchange definitions and setup
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

from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI


class CoinbasePro(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "coinbase_pro", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'coinbase_pro', ['API_KEY', 'API_SECRET', 'API_PASS',
                                                                           'sandbox'])

        sandbox = super().evaluate_sandbox(auth)

        keys = auth.keys
        if sandbox:
            calls = CoinbaseProAPI(api_key=keys['API_KEY'],
                                   api_secret=keys['API_SECRET'],
                                   api_pass=keys['API_PASS'],
                                   api_url="https://api-public.sandbox.pro.coinbase.com/")
        else:
            # Create the authenticated object
            calls = CoinbaseProAPI(api_key=keys['API_KEY'],
                                   api_secret=keys['API_SECRET'],
                                   api_pass=keys['API_PASS'])

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
        return self.interface.get_products()

    def get_direct_calls(self) -> CoinbaseProAPI:
        return self.calls

    """
    GUI Testing Functions | These only exist in the coinbase_pro class:
    """

    def get_indicators(self):
        return self.calls.get_products()

    def filter_relevant(self, dict):
        """
        Currently unused. Will be used for filtering for user-relevant currencies

        Args:
            dict: Dictionary to filter important currencies from

        Returns:
            list: filtered information about the account dictionary
        """
        self.get_state()
        self.__readable_state = {}
        unused = {}
        for i in range(len(self.__state)):
            value = float((self.__state[i]["balance"]))
            if value > 0:
                self.__readable_state[self.__state[i]["currency"]] = {
                    "Qty:": value,
                }
                currency = (self.__state[i]["currency"])
                # There can be no currency state until a model is added to the currency
                try:
                    self.__readable_state[self.__state[i]["currency"]] = {
                        **self.__readable_state[self.__state[i]["currency"]], **self.get_model_state(currency)}
                except KeyError as e:
                    pass
            else:
                unused[self.__state[i]["currency"]] = {
                    "Qty:": 0,
                }
        return self.__readable_state
