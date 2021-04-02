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

from Blankly.exchange import Exchange
from Blankly.Coinbase_Pro.Coinbase_Pro_API import API
from Blankly.API_Interface import APIInterface as Interface
import Blankly.auth_constructor


class Coinbase_Pro(Exchange):
    def __init__(self, portfolio_name=None, auth_path="Keys.json"):
        # Load the auth from the keys file
        auth, defined_name = Blankly.auth_constructor.load_auth_coinbase_pro(auth_path, portfolio_name)
        self.__calls = API(auth[0], auth[1], auth[2])
        Exchange.__init__(self, "coinbase_pro", defined_name)

        # Create the authenticated object
        fees = self.__calls.get_fees()
        exchange_properties = {
            "maker_fee_rate": fees['maker_fee_rate'],
            "taker_fee_rate": fees['taker_fee_rate']
        }
        self.__Interface = Interface("coinbase_pro", self.__calls, exchange_properties)
        self.get_state()

        # Create the model container
        self.models = {}

    def append_model(self, model, coin, args=None, id=None):
        """
        Append the models to the exchange, these can be run
        """
        coin_id = coin + "-" + self.preferences["settings"]["base_currency"]
        added_model = model
        self.models[coin] = {
            "model": added_model,
            "args": args
        }
        model.setup("coinbase_pro", coin, coin_id, self.preferences, self.get_currency_state(coin),
                    self.__Interface)

    def get_model(self, coin):
        return self.models[coin]["model"]

    def get_indicators(self):
        return self.__calls.get_fees()

    """
    Exchange and model state management.
    """

    def get_model_state(self, currency):
        return (self.get_model(currency)).get_state()

    def get_state(self):
        """
        Calls to to the interface to receive info on all currencies.
        """
        self.__state = self.__calls.get_accounts()
        return self.__state

    def get_portfolio_state(self):
        """
        Portfolio state is the internal properties for the exchange block.
        """
        self.get_state()
        return self.__state

    def get_currency_state(self, currency):
        """
        State for just this new currency

        Args:
            currency: Currency to filter for. This filters model information and the exchange information.
        """
        portfolio_state = self.get_portfolio_state()
        slice = None
        for i in portfolio_state:
            if i["currency"] == currency:
                slice = i
                break

        return {
            "account": slice,
            "model": self.get_model_state(currency)
        }

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.__calls.get_fees()

    """
    For future use
    """
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
