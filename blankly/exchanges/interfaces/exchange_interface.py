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

import blankly.utils.utils as utils
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
import abc
import time


# TODO: need to add a cancel all orders function
class ExchangeInterface(ABCExchangeInterface, abc.ABC):
    def __init__(self, exchange_name, authenticated_API, preferences_path=None):
        self.exchange_name = exchange_name
        self.calls = authenticated_API
        # Reload user preferences here
        self.user_preferences = utils.load_user_preferences(preferences_path)

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
                ["symbol", str],
                ["base_asset", str],
                ["quote_asset", str],
                ["base_min_size", float],
                ["base_max_size", float],
                ["base_increment", float]
            ],
            'get_account': [
                ["symbol", str],
                ["available", float],
                ["hold", float]
            ],
            'market_order': [
                ["symbol", str],
                ["id", str],
                ["created_at", float],
                ["funds", float],
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
            'get_asset_limits': [
                ["symbol", str],
                ["base_asset", str],
                ["quote_asset", str],
                ["base_min_size", float],  # Minimum size to buy
                ["base_max_size", float],  # Maximum size to buy
                ["quote_increment", float],  # Specifies the min order price as well as the price increment.
                ["base_increment", float],  # Specifies the minimum increment for the base_asset.
                ["max_orders", int],
                ["min_market_funds", float],
                ["max_market_funds", float],
                ["min_price", float],
                ["max_price", float],
                ["fractional_limit", bool]
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
             The exchange's direct calls object. A blankly Bot class should have immediate access to this by
             default
        """
        return self.calls

    """ Needs to be overridden here """

    def get_exchange_type(self):
        return self.exchange_name

    @property
    def account(self):
        return self.get_account()

    @property
    def orders(self):
        return self.get_open_orders()

    @property
    def cash(self):
        using_setting = self.user_preferences['settings'][self.exchange_name]['cash']
        return self.get_account(using_setting)['available']

    def history(self, symbol: str, to=200, resolution: str='1d', start_date=None, end_date=None):
        if end_date is None:
            epoch_stop = time.time()
        else:
            epoch_stop = utils.convert_input_to_epoch(end_date)

        # convert resolution into epoch seconds    
        resolution_seconds = time_interval_to_seconds(resolution)

        if start_date is None:
            if isinstance(to, int):
                # use number of points to calculate the start epoch
                epoch_start = epoch_stop - to * resolution_seconds
            else:
                epoch_start = epoch_stop - time_interval_to_seconds(to)
        else:
            epoch_start = utils.convert_input_to_epoch(start_date)

        return self.get_product_history(symbol, epoch_start, epoch_stop, resolution_seconds)

    def get_account(self, symbol=None):
        """
        Get all assets in an account, or sort by assets/account_id
        Args:
            symbol (Optional): Filter by particular symbol

        Coinbase Pro: get_account
        binance: get_account["balances"]
        """

        if symbol is not None:
            symbol = utils.get_base_asset(symbol)

        return symbol

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        return utils.convert_epochs(epoch_start), utils.convert_epochs(epoch_stop)

    def choose_order_specificity(self, order_type):
        # This lower should not be necessary if everything is truly homogeneous
        order_type = order_type.lower()
        if order_type == 'market':
            return self.needed['market_order']
        elif order_type == 'limit':
            return self.needed['limit_order']
        else:
            return self.needed['market_order']

    def homogenize_order_status(self, exchange, status):
        if exchange == "binance":
            if status == "new":
                return "open"

        return status
