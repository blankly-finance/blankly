"""
    FTX definition & setup
    Copyright (C) 2021 Blankly Finance

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


from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.ftx.ftx_api import FTXAPI


class FTX(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        # Giving the preferences path as none allows us to create a default
        Exchange.__init__(self, "ftx", portfolio_name, keys_path, settings_path)

    """
    Builds information about the asset on this exchange by making particular API calls
    """

    def get_asset_state(self, symbol):
        """
        This determines the internal properties of the exchange block.
        Should be implemented per-class because it requires different types of interaction with each exchange.
        """
        # TODO Populate this with useful information
        return self.interface.get_account(symbol)

    def get_exchange_state(self):
        """
        Exchange state is the external properties for the exchange block
        """
        # TODO Populate this with useful information
        return self.interface.get_fees()

    def get_direct_calls(self) -> FTXAPI:
        return self.calls
