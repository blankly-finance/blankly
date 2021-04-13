"""
    Inherited object to allow library interaction with a Blankly bot
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

from multiprocessing import Process, Manager
import Blankly
import abc
import copy
import warnings


class BlanklyBot(abc.ABC):
    def __init__(self):
        """
        Initialize state variables when the bot is created
        """
        # If the start is called again, this will make sure multiple processes don't start
        self.__state = {}
        self.initial_state = None
        self.exchange_type = ""
        self.coin = ""
        self.user_preferences = {}
        self.Interface = None
        self.coin_id = ""
        self.default_ticker = None
        self.Ticker_Manager = None
        self.direct_calls = None
        self.process = Process(target=self.setup_process)

    def setup(self, exchange_type, coin, coin_id, user_preferences, initial_state, interface):
        """
        This function is populated by the exchange.
        Args:
            exchange_type (str): Type of exchange i.e "binance" or "coinbase_pro"
            coin: Type of coin, i.e "BTC"
            coin_id: Identifier for the coin market, i.e "BTC-USD"
            user_preferences: Dictionary with the defined preferences
            initial_state: Information about the account the model is defaulted to running on
            interface: Object for consistent trading on the supported exchanges
        """
        # Shared variables with the processing a manager
        self.initial_state = initial_state
        self.__state = Manager().dict({})
        self.exchange_type = exchange_type
        self.coin = coin
        self.user_preferences = user_preferences
        # TODO. This copy is a bad solution. It generally means that there will be a ticker object used on each process.
        #  The worry is that if we implement auto rate limits, each process won't know whats going on. This might need
        #  to be the case however to keep things static
        self.Interface = copy.deepcopy(interface)
        # Coin id is the currency and which market its on
        self.coin_id = coin_id
        self.direct_calls = interface.get_calls()

    def is_running(self):
        """
        This function returns the status of the process. This ensures that two processes cannot be started on the same
        account.
        """
        return self.process.is_alive()

    def run(self, args):
        """
        Called when the user starts the model. This is what begins and manages the process.
        """
        # Start the setup process and then call the main
        p = Process(target=self.setup_process, args=(args,))
        self.process = p
        self.process.start()

    def setup_process(self, args):
        """
        Create any objects that need to be process-specific in the other process
        """
        self.Ticker_Manager = Blankly.TickerManager(self.exchange_type, self.coin_id)
        self.default_ticker = self.Ticker_Manager.create_ticker(self.price_event)
        self.Interface.append_ticker_manager(self.Ticker_Manager)
        self.main(args)

    """
    State getters and setters for external understanding of the operation
    """
    def get_state(self):
        return self.__state.copy()

    def update_state(self, key, value):
        """
        This function adds or removes state values from the state dictionary
        Args:
            key: The key value to be added/changed
            value: The value the key should be set to
        """
        self.__state[key] = value

    def remove_key(self, key):
        """
        This function removes a key from the state variable
        Args:
            key: This specifies the key value to remove from the state dictionary
        """
        self.__state.pop(key)

    @abc.abstractmethod
    def main(self, args):
        warnings.warn("No user-created main function to run, stopping...")

    @abc.abstractmethod
    def price_event(self, tick):
        pass

    @abc.abstractmethod
    def orderbook_event(self, tick):
        pass
