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


class BlanklyBot:
    def __init__(self):
        """
        Initialize state variables
        """
        # If the start is called again, this will make sure multiple processes don't start
        self.__is_running = False
        self.__state = {}
        self.exchange_type = ""
        self.coin = ""
        self.user_preferences = {}
        self.Interface = None
        self.coin_id = ""
        self.default_ticker = None
        self.Ticker_Manager = None

    def setup(self, exchange_type, coin, user_preferences, initial_state, interface):
        """
        This function is populated by the exchange.
        """
        # Shared variables with the processing a manager
        self.__state = Manager().dict(initial_state)
        self.exchange_type = exchange_type
        self.coin = coin
        self.user_preferences = user_preferences
        self.Interface = interface

        # Coin id is the currency and which market its on
        self.coin_id = coin + "-" + user_preferences["settings"]["base_currency"]
        # Create the ticker for this kind of currency. Callbacks will occur in the "price_event" function
        self.Ticker_Manager = Blankly.TickerInterface(self.exchange_type)
        self.default_ticker = self.Ticker_Manager.create_ticker(self.coin_id, self)

    # Make sure the process knows that this model is on, removing this off could result in many threads
    def is_running(self):
        return self.__is_running

    def run(self, args):
        """
        Called by GUI when the user starts the model
        """
        # Start the process
        if args is None:
            p = Process(target=self.main)
        else:
            p = Process(target=self.main, args=args)
        self.__is_running = True
        p.start()

    """
    State getters and setters for writing to the GUI or as state updates
    """

    def get_state(self):
        return self.__state

    def update_state(self, key, value):
        self.__state[key] = value

    def remove_key(self, key):
        self.__state.pop(key)

