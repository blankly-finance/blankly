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


from Blankly.exchanges.interfaces.paper_trade.paper_trade_interface import PaperTradeInterface
from Blankly.exchanges.exchange import Exchange


class PaperTrade(Exchange):
    def __init__(self, authenticated_exchange: Exchange, initial_account_values: dict = None):
        # Giving the preferences path as none allows us to create a default
        Exchange.__init__(self, "paper_trade", "", None, None)

        self.Interface = PaperTradeInterface(authenticated_exchange.get_interface(), initial_account_values)
        self.calls = authenticated_exchange.get_direct_calls()

    """
    Builds information about the symbol on this exchange by making particular API calls
    """
    def get_asset_state(self, symbol):
        """
        This determines the internal properties of the exchange block.
        Should be implemented per-class because it requires different types of interaction with each exchange.
        """
        # TODO Populate this with useful information
        return self.Interface.get_account(symbol)

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.Interface.get_fees()

    def get_direct_calls(self):
        return self.calls
