"""
    Binance exchange definitions and setup
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

from Blankly.exchanges.exchange import Exchange
import Blankly.auth_constructor
import Blankly.utils.utils as utils

from binance.client import Client
import warnings


class Binance(Exchange):
    def __init__(self, portfolio_name=None, auth_path="Keys.json", preferences_path=None):
        # Load the auth from the keys file
        auth, defined_name = Blankly.auth_constructor.load_auth_binance(auth_path, portfolio_name)

        Exchange.__init__(self, "binance", defined_name, preferences_path)

        preferences = utils.load_user_preferences()
        if preferences["settings"]["use_sandbox"]:
            warnings.warn("Binance sandbox authentication not yet supported")
        else:
            pass
        self.__calls = Client(api_key=auth[0], api_secret=auth[1],
                              tld=self.get_preferences()["settings"]["binance_tld"])

        Blankly.auth_constructor.write_auth_cache("binance", defined_name, self.__calls)

        self.construct_interface(self.__calls)

    """
    Builds information about the currency on this exchange by making particular API calls
    """
    def get_currency_state(self, currency):
        """
        Portfolio state is the internal properties for the exchange block.
        """
        # TODO Populate this with useful information
        currency = Blankly.utils.get_base_currency(currency)
        account = self.Interface.get_account(currency=currency)
        return account

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.Interface.get_fees()

    def get_direct_calls(self) -> Client:
        return self.__calls
