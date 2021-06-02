"""
    Logic to provide consistency across exchanges
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


import Blankly.utils.utils as utils
from Blankly.interface.abc_currency_interface import ICurrencyInterface
import abc
import sys


# TODO: need to add a cancel all orders function
class CurrencyInterface(ICurrencyInterface, abc.ABC):
    def __init__(self, exchange_name, authenticated_API):
        self.exchange_name = exchange_name
        self.calls = authenticated_API
        # Reload user preferences here
        self.user_preferences = utils.load_user_preferences()

        # TODO, improve creation of its own properties
        self.exchange_properties = None
        # Some exchanges like binance will not return a value of 0.00 if there is no balance
        self.available_currencies = {}
        self.init_exchange()

        self.needed = {
            '__init_exchange__': [
                ['maker_fee_rate', float],
                ['taker_fee_rate', float]
            ],
            'get_products': [
                ["currency_id", str],
                ["base_currency", str],
                ["quote_currency", str],
                ["base_min_size", float],
                ["base_max_size", float],
                ["base_increment", float]
            ],
            'get_account': [
                ["currency", str],
                ["available", float],
                ["hold", float]
            ],
            'market_order': [
                ["product_id", str],
                ["id", str],
                ["created_at", float],
                ["funds", float],
                ["status", str],
                ["type", str],
                ["side", str]
            ],
            'limit_order': [
                ["product_id", str],
                ["id", str],
                ["created_at", float],
                ["price", float],
                ["size", float],
                ["status", str],
                ["time_in_force", str],
                ["type", str],
                ["side", str]
            ],
            'stop_limit': [
                ["product_id", str],
                ["id", str],
                ["created_at", float],
                ["stop_price", float],
                ["limit_price", float],
                ["stop", str],
                ["size", float],
                ["status", str],
                ["time_in_force", str],
                ["type", str],
                ["side", str]
            ],
            'cancel_order': [
                ['order_id', str]
            ],
            'get_open_orders': [
                ["id", str],
                ["price", float],
                ["size", float],
                ["type", str],
                ["side", str],
                ["status", str],
                ["product_id", str]
            ],
            'get_order': [
                ["id", str],
                ["product_id", str],
                ["price", float],
                ["size", float],
                ["type", str],
                ["side", str],
                ["status", str],
                ["funds", float]
            ],
            'get_fees': [
                ['maker_fee_rate', float],
                ['taker_fee_rate', float]
            ],
            'get_market_limits': [
                ["market", str],
                ["base_currency", str],
                ["quote_currency", str],
                ["base_min_size", float],  # Minimum size to buy
                ["base_max_size", float],  # Maximum size to buy
                ["quote_increment", float],  # Specifies the min order price as well as the price increment.
                ["base_increment", float],  # Specifies the minimum increment for the base_currency.
                ["max_orders", int],
                ["min_price", float],
                ["max_price", float]
            ]
        }

    @abc.abstractmethod
    def init_exchange(self):
        """
        Create the properties for the exchange.
        """
        pass

    """ Needs to be overridden here """
    def get_calls(self):
        """
        Returns:
             The exchange's direct calls object. A Blankly Bot class should have immediate access to this by
             default
        """
        return self.calls

    """ Needs to be overridden here """
    def get_exchange_type(self):
        return self.exchange_name

    def get_account(self, currency=None):
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency (Optional): Filter by particular currency

        Coinbase Pro: get_account
        Binance: get_account["balances"]
        """

        if currency is not None:
            currency = utils.get_base_currency(currency)

        return currency

    def get_product_history(self, product_id, epoch_start, epoch_stop, granularity):
        return utils.convert_epochs(epoch_start), utils.convert_epochs(epoch_stop)

    def update_progress(self, progress):
        # update_progress() : Displays or updates a console progress bar
        # Accepts a float between 0 and 1. Any int will be converted to a float.
        # A value under 0 represents a 'halt'.
        # A value at 1 or bigger represents 100%
        bar_length = 10  # Modify this to change the length of the progress bar
        status = ""
        if isinstance(progress, int):
            progress = float(progress)
        if not isinstance(progress, float):
            progress = 0
            status = "error: progress var must be float\r\n"
        if progress < 0:
            progress = 0
            status = "Halt...\r\n"
        if progress >= 1:
            progress = 1
            status = "Done...\r\n"
        block = int(round(bar_length * progress))
        text = "\rPercent: [{0}] {1}% {2}".format("#" * block + "-" * (bar_length - block), progress * 100, status)
        sys.stdout.write(text)
        sys.stdout.flush()
