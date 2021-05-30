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
import typing

import pandas

from Blankly.utils.time_builder import time_interval_to_seconds
from Blankly.exchanges.exchange import Exchange
from Blankly.exchanges.Paper_Trade.Paper_Trade_Interface import PaperTradeInterface
from Blankly.exchanges.Paper_Trade.backtest_controller import BackTestController
from Blankly.exchanges.exchange import Exchange

import pandas as pd


class PaperTrade(Exchange):
    def __init__(self, authenticated_exchange: Exchange):
        # Giving the preferences path as none allows us to create a default
        Exchange.__init__(self, "paper_trade", "", None)

        self.backtest_price_events = []
        self.price_data = {}

        self.Interface = PaperTradeInterface(authenticated_exchange.get_interface())

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

    def append_backtest_price_data(self, asset_id, price_data: pandas.DataFrame):
        if isinstance(price_data, str):
            price_data = pd.read_csv(price_data)
        elif isinstance(price_data, pandas.DataFrame):
            pass
        else:
            raise TypeError("Price data is not of type str or dataframe.")
        self.price_data[asset_id] = price_data

    def append_backtest_price_event(self, callback: typing.Callable, asset_id, time_interval):
        if isinstance(time_interval, str):
            time_interval = time_interval_to_seconds(time_interval)
        self.backtest_price_events.append([callback, asset_id, time_interval])

    def backtest(self):
        # Create arrays of price events along with their interval

        # Create a new controller
        if self.price_data == {} or self.backtest_price_events == []:
            raise ValueError("Either no price data or backtest events given. "
                             "Use .append_backtest_price_data or "
                             "append_backtest_price_event to create the backtest model.")
        else:
            controller = BackTestController(self.get_interface(), self.price_data, self.backtest_price_events)

        # Run the controller
        return controller.run()

    def get_direct_calls(self):
        return None
