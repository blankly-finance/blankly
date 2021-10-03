"""
    Inherited object to allow library interaction with a blankly bot
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

import copy
from multiprocessing import Manager, Process

from binance.client import Client as Binance_API

import blankly
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI
from blankly.exchanges.managers.orderbook_manager import OrderbookManager
from blankly.exchanges.managers.ticker_manager import TickerManager
from blankly.utils.utils import info_print


class BlanklyBot:
    symbol: str
    user_preferences: dict
    exchange_type: str
    initial_state: dict
    # Define the given types for the user
    orderbook_manager: OrderbookManager
    ticker_manager: TickerManager
    interface: ABCExchangeInterface
    coinbase_pro_direct: CoinbaseProAPI
    binance_direct: Binance_API

    def __init__(self):
        """
        Initialize state variables when the bot is created
        """
        # If the start is called again, this will make sure multiple processes don't start
        self.__state = {}
        self.coin = ""
        self.exchange_type = ""
        self.initial_state = {}
        self.user_preferences = {}
        self.symbol = ""
        self.direct_calls = None
        self.process = Process(target=self.setup_process)

    def setup(self, exchange_type, currency_pair, user_preferences, initial_state, interface):
        """
        This function is populated by the exchange.
        Args:
            exchange_type (str): Type of exchange i.e "binance" or "coinbase_pro"
            currency_pair: Identifier for the coin market, i.e "BTC-USD"
            user_preferences: Dictionary with the defined preferences
            initial_state: Information about the account the model is defaulted to running on
            interface: Object for consistent trading on the supported exchanges
        """
        # Shared variables with the processing a manager
        self.initial_state = initial_state
        self.__state = Manager().dict({})
        self.exchange_type = exchange_type
        self.user_preferences = user_preferences
        self.interface = copy.deepcopy(interface)
        # Coin id is the currency and which market its on
        self.symbol = currency_pair
        self.direct_calls = interface.get_calls()
        self.coinbase_pro_direct = self.direct_calls
        self.binance_direct = self.direct_calls

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
        self.ticker_manager = blankly.TickerManager(self.exchange_type, self.symbol)
        self.orderbook_manager = blankly.OrderbookManager(self.exchange_type, self.symbol)
        self.main(args)

    """
    State getters and setters for external understanding of the operation
    """

    def get_state(self):
        try:
            return self.__state.copy()
        except BrokenPipeError:
            raise BrokenPipeError("Broken Pipe. Is the main process still running?")

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

    def main(self, args):
        info_print("No user-created main function to run, stopping...")
