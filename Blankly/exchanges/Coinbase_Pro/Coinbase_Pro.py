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

from Blankly.exchanges.exchange import Exchange
from Blankly.exchanges.Coinbase_Pro.Coinbase_Pro_API import API
from Blankly.API_Interface import APIInterface as Interface
import Blankly.auth_constructor


class Coinbase_Pro(Exchange):
    def __init__(self, portfolio_name=None, auth_path="Keys.json"):
        # Load the auth from the keys file
        auth, defined_name = Blankly.auth_constructor.load_auth_coinbase_pro(auth_path, portfolio_name)
        self.__calls = API(auth[0], auth[1], auth[2])
        Exchange.__init__(self, "coinbase_pro", defined_name)

        # Create the authenticated object
        self.Interface = Interface("coinbase_pro", self.__calls)

        # Create the model container
        self.models = {}

    """
    Builds information about the currency on this exchange by making particular API calls
    """
    def get_currency_state(self, currency):
        """
        This determines the internal properties of the exchange block.
        Should be implemented per-class because it requires different types of interaction with each exchange.
        """
        # TODO Populate this with useful information
        return self.Interface.get_account(currency)

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.Interface.get_fees()

    """
    GUI Testing Functions | These only exist in the Coinbase_Pro class:
    """
    def get_indicators(self):
        return self.__calls.get_fees()

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
