"""
    Keyless exchange definition & setup
    Copyright (C) 2022 Emerson Dove

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

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.paper_trade.paper_trade_interface import PaperTradeInterface
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.exchanges.interfaces.keyless.keyless_api import KeylessAPI


class KeylessExchange(Exchange):
    def __init__(self, maker_fee=0, taker_fee=0, portfolio_name=None, settings_path=None):
        Exchange.__init__(self, "keyless", portfolio_name, settings_path)

        self.calls = KeylessAPI(maker_fee, taker_fee)

        self.interface = PaperTradeInterface(self.calls)

        # This one must be exported manually
        blankly.reporter.export_used_exchange("keyless")

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
        return self.interface.get_products()

    def get_direct_calls(self) -> ABCExchangeInterface:
        return self.calls
