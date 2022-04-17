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

import abc

import blankly.utils.utils as utils
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface


# TODO: need to add a cancel all orders function
class ExchangeInterface(ABCExchangeInterface, abc.ABC):
    def __init__(self, exchange_name, authenticated_api, preferences_path=None, valid_resolutions=None):
        self.exchange_name = exchange_name
        self.calls = authenticated_api
        self.valid_resolutions = valid_resolutions
        # Reload user preferences here
        self.user_preferences = utils.load_user_preferences(preferences_path)

        self.exchange_properties = None
        # Some exchanges like binance will not return a value of 0.00 if there is no balance
        self.available_currencies = {}

        self.needed = {
            '__init_exchange__': [
                ['maker_fee_rate', float],
                ['taker_fee_rate', float]
            ],
            'get_products': [
                ["symbol", str],
                ["base_asset", str],
                ["quote_asset", str],
                ["base_min_size", float],
                ["base_max_size", float],
                ["base_increment", float]
            ],
            'get_account': [
                ["available", float],
                ["hold", float]
            ],
            'market_order': [
                ["symbol", str],
                ["id", str],
                ["created_at", float],
                ["size", float],
                ["status", str],
                ["type", str],
                ["side", str]
            ],
            'limit_order': [
                ["symbol", str],
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
                ["symbol", str],
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
            # 'get_open_orders': [  # Key specificity changes based on order type
            #     ["id", str],
            #     ["price", float],
            #     ["size", float],
            #     ["type", str],
            #     ["side", str],
            #     ["status", str],
            #     ["product_id", str]
            # ],
            # 'get_order': [
            #     ["product_id", str],
            #     ["id", str],
            #     ["price", float],
            #     ["size", float],
            #     ["type", str],
            #     ["side", str],
            #     ["status", str],
            #     ["funds", float]
            # ],
            'get_fees': [
                ['maker_fee_rate', float],
                ['taker_fee_rate', float]
            ],
            'get_order_filter': [
                ["symbol", str],
                ["base_asset", str],
                ["quote_asset", str],
                ["max_orders", int],
                ["limit_order", dict],
                ["market_order", dict]
            ]
        }

        if self.user_preferences['settings']['test_connectivity_on_auth']:
            self.init_exchange()

    @abc.abstractmethod
    def init_exchange(self):
        """
        Create the properties for the exchange.

        This is never run if test_connectivity_on_auth is set to false
        """
        pass

    """ Needs to be overridden here """

    def get_calls(self):
        """
        Returns:
             The exchange's direct calls object. A blankly Bot class should have immediate access to this by
             default
        """
        return self.calls

    """ Needs to be overridden here """

    def get_exchange_type(self):
        return self.exchange_name

    @property
    def account(self):
        return utils.AttributeDict(self.get_account())

    @property
    def orders(self):
        return self.get_open_orders()

    @property
    def cash(self):
        using_setting = self.user_preferences['settings'][self.exchange_name]['cash']
        return self.get_account(using_setting)['available']

    def is_backtesting(self):
        """
        Overridden by interfaces which have a valid backtesting boolean value
        """
        return None

    @staticmethod
    def evaluate_multiples(valid_resolutions: list, resolution_seconds: float):
        found_multiple = -1
        for multiple in reversed(valid_resolutions):
            if resolution_seconds % multiple == 0:
                found_multiple = multiple
                break
        if found_multiple < 0:
            raise ValueError("This exchange currently does not support this specific resolution, try making it a "
                             "multiple of 1 minute, 1 hour or 1 day")

        row_divisor = resolution_seconds / found_multiple
        row_divisor = int(row_divisor)

        if row_divisor > 100:
            raise Warning("The resolution you requested is an extremely high of the base resolutions supported and may "
                          "slow down the performance of your model: {} * {}".format(found_multiple, row_divisor))

        return found_multiple, row_divisor

    def get_account(self, symbol=None):
        """
        This method is a helper that allows the get_account functions to assume the base asset is being passed in
        Args:
            symbol (Optional): Filter by particular symbol

        Coinbase Pro: get_account
        binance: get_account["balances"]
        """

        if symbol is not None:
            symbol = utils.get_base_asset(symbol)

        return symbol

    def choose_order_specificity(self, order_type):
        # This lower should not be necessary if everything is truly homogeneous
        order_type = order_type.lower()
        if order_type == 'market':
            return self.needed['market_order']
        elif order_type == 'limit':
            return self.needed['limit_order']
        else:
            return self.needed['market_order']

    """
    Order lifecycle should be:
    Accepted -> live -> done -> settled
    """

    @staticmethod
    def homogenize_order_status(exchange, status):
        if exchange == "binance":
            if status == "new":
                return "open"
        elif exchange == 'alpaca':
            if status == 'accepted':
                return 'accepted'
            if status == 'new':
                return 'new'

        return status
