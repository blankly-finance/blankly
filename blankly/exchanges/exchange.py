"""
    Inherited exchange object.
    Copyright (C) 2021  Emerson Dove, Arun Annamalai, Brandon Fan

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
import abc
import time

import blankly
from blankly.exchanges.abc_exchange import ABCExchange
from blankly.exchanges.auth.auth_constructor import write_auth_cache
from blankly.exchanges.auth.auth_factory import AuthFactory
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.exchanges.interfaces.binance.binance_interface import BinanceInterface
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_interface import CoinbaseProInterface
from blankly.exchanges.interfaces.direct_calls_factory import DirectCallsFactory


class Exchange(ABCExchange, abc.ABC):
    interface: ABCExchangeInterface

    def __init__(self, exchange_type, portfolio_name, keys_path, preferences_path):
        self.__type = exchange_type  # coinbase_pro, binance, alpaca, oanda
        self.__name = portfolio_name  # my_cool_portfolio
        self.__factory = AuthFactory()

        self.__auth = self.__factory.create_auth(keys_path, self.__type, self.__name)
        self.__direct_calls_factory = DirectCallsFactory()
        self.calls, self.interface = self.__direct_calls_factory.create(self.__type, self.__auth, preferences_path)
        write_auth_cache(exchange_type, portfolio_name, self.calls)

        self.preferences = blankly.utils.load_user_preferences(preferences_path)

        # Create the model container
        self.models = {}

    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

    def get_preferences(self):
        return self.preferences

    # Can be removed?
    def construct_interface(self, calls):
        if self.__type == "coinbase_pro":
            self.interface = CoinbaseProInterface(self.__type, calls)
        elif self.__type == "binance":
            self.interface = BinanceInterface(self.__type, calls)

    def get_interface(self) -> ABCExchangeInterface:
        """
        Get the the authenticated interface for the object. This will provide authenticated API calls.
        """
        return self.interface

    def start_models(self, symbol=None):
        """
        Start all models or a specific one after appending it to to the exchange.

        This is used only for multiprocessed bots which are appended directly to the exchange. NOT bots that use
        the strategy class.
        """
        if symbol is not None:
            # Run a specific model with the args
            if not self.models[symbol]["model"].is_running():
                self.models[symbol]["model"].run(self.models[symbol]["args"])
        else:
            for coin_iterator in self.models:
                # Start all models
                if not self.models[coin_iterator]["model"].is_running():
                    self.models[coin_iterator]["model"].run(self.models[coin_iterator]["args"])
                    # There is some delay. Optimally the bots should be started in a different thread so this doesn't
                    # block the main
                    time.sleep(.1)
                else:
                    print("Ignoring the model on " + coin_iterator)

    def __get_model(self, coin):
        """
        Get the model to reference to
        """
        return self.models[coin]["model"]

    def get_model_state(self, symbol):
        """
        Returns JUST the model state, as opposed to all the data returned by get_asset_state()

        This is also used for querying a general state from a multiprocessed bot
        Args:
            symbol: Currency that the selected model is running on.
        """
        return (self.__get_model(symbol)).get_state()

    def get_full_state(self, symbol):
        """
        Makes API calls to determine the state of the currency. This also returns the state of the model on that
        currency.

        This is also used only for multiprocessed models

        Args:
            symbol: Currency to filter for. This filters model information and the exchange information.
        """
        state = self.get_asset_state(symbol)

        return {
            "account": state,
            "model": self.get_model_state(symbol)
        }

    def write_value(self, symbol, key, value):
        """
        Write a key/value pair to a bot attached to a particular currency pair

        This is also used only for multiprocessed bots.

        Args:
            symbol: Change state on bot attached to this currency
            key: Key to assign a value to
            value: Value to assign to the key
        """
        self.__get_model(symbol).update_state(key, value)

    def append_model(self, model, symbol, args=None):
        """
        Append the models to the exchange, these can be run
        Args:
            model: Model object to be used. This is objects inheriting blankly_bot
            symbol: the currency to use, such as "BTC-USD"
            args: Args to pass into the model when it is run. This can be any datatype, the object is passed
        """
        added_model = model
        self.models[symbol] = {
            "model": added_model,
            "args": args
        }
        model.setup(self.__type, symbol, self.preferences, self.get_full_state(symbol),
                    self.interface)

    @abc.abstractmethod
    def get_asset_state(self, symbol):
        """
        This is left out of documentation because it lacks thorough implementations.

        Generally this will be used to get a report of performance of a symbol on an exchange.
        """
        pass

    @abc.abstractmethod
    def get_direct_calls(self):
        pass
