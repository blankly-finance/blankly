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
from Blankly.exchanges.Paper_Trade.Paper_Trade_Interface import PaperTradeInterface
import pandas as pd


class PaperTrade(Exchange):
    def __init__(self, authenticated_interface):
        # Giving the preferences path as none allows us to create a default
        Exchange.__init__(self, "paper_trade", "", None)

        self.Interface = PaperTradeInterface(authenticated_interface)

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

    def backtest(self,
                 price_data,
                 asset_id,
                 price_event=None,
                 orderbook_event=None,
                 news_data=None):
        if isinstance(price_data, str):
            col_list = ["price"]
            prices = pd.read_csv(price_data, usecols=col_list).price.tolist()
        elif isinstance(price_data, list):
            prices = price_data
        else:
            raise TypeError("Price data is not of type str path or list")

        # Convert interface to backtesting
        self.get_interface().setup_backtesting()

        for i in prices:
            price_event(i, asset_id)

    def get_direct_calls(self):
        return None
