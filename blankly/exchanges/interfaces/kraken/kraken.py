"""
    Kraken definition & setup
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


from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.kraken.kraken_api import API as KrakenAPI
from blankly.exchanges.auth.auth_constructor import AuthConstructor
from blankly.utils import info_print
from blankly.exchanges.interfaces.paper_trade.paper_trade_interface import PaperTradeInterface
from blankly.exchanges.interfaces.kraken.kraken_interface import KrakenInterface


class Kraken(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "kraken", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'kraken', ['API_KEY', 'API_SECRET', 'sandbox'])

        keys = auth.keys
        sandbox = super().evaluate_sandbox(auth)

        calls = KrakenAPI(keys['API_KEY'], keys['API_SECRET'])

        # Always finish the method with this function
        super().construct_interface_and_cache(calls)

        # Kraken is unique because we can continue by wrapping the interface in paper trade
        if sandbox:
            info_print('The sandbox setting is enabled for this key. Kraken has been created as a '
                       'paper trading instance.')
            self.interface = PaperTradeInterface(KrakenInterface(calls, settings_path))

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

    def get_direct_calls(self) -> KrakenAPI:
        return self.calls
