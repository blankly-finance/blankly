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
import time
import warnings
from datetime import datetime as dt
from typing import Union
from collections import deque

import numpy
import pandas as pd
from dateutil import parser

import blankly.utils.utils as utils
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.utils.time_builder import time_interval_to_seconds


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

    def history(self,
                symbol: str,
                to: Union[str, int] = 200,
                resolution: Union[str, float] = '1d',
                start_date: Union[str, dt, float] = None,
                end_date: Union[str, dt, float] = None,
                return_as: str = 'df'):

        is_backtesting = self.is_backtesting()
        if is_backtesting is not None and end_date is None:
            # is_backtesting can only return a non None value if a function overrides the is_backtesting function
            #  and says its backtesting by returning a valid time
            end_date = is_backtesting

        if start_date is not None and end_date is not None:
            to = None

        to_present = False
        if end_date is None:
            to_present = True

        # convert resolution into epoch seconds
        resolution_seconds = int(time_interval_to_seconds(resolution))

        if end_date is None:
            # Figure out the next point and then subtract to the last stamp
            most_recent_valid_resolution = utils.ceil_date(dt.now(),
                                                           seconds=resolution_seconds).timestamp() - resolution_seconds
            # Binance is nice enough to update OHLCV data so we have to exclude that by subtracting a resolution
            epoch_stop = most_recent_valid_resolution - resolution_seconds
            count_from = most_recent_valid_resolution
        else:
            if isinstance(end_date, str):
                parsed_date = parser.parse(end_date)
            elif isinstance(end_date, float) or isinstance(end_date, numpy.int64) or isinstance(end_date, int):
                parsed_date = dt.fromtimestamp(end_date)
            else:
                parsed_date = end_date
            valid_time_in_past = utils.ceil_date(parsed_date,
                                                 seconds=resolution_seconds).timestamp() - resolution_seconds
            epoch_stop = valid_time_in_past - resolution_seconds
            count_from = valid_time_in_past

        if start_date is None and end_date is None:
            if isinstance(to, int):
                # use number of points to calculate the start epoch
                epoch_start = count_from - (to * resolution_seconds)
            else:
                epoch_start = count_from - time_interval_to_seconds(to)
        elif start_date is None and end_date is not None:
            if isinstance(to, int):
                epoch_start = count_from - (to * resolution_seconds)
            else:
                epoch_start = count_from - time_interval_to_seconds(to)
        else:
            epoch_start = utils.convert_input_to_epoch(start_date)

        response = self.overridden_history(symbol, epoch_start, epoch_stop, resolution_seconds, to=to,)

        # Add a check to make sure that coinbase pro has updated
        if to_present and self.get_exchange_type() == "coinbase_pro":
            data_append = None
            tries = 0
            while True:
                if data_append is None:
                    # We can continue if this is valid
                    if response['time'].iloc[-1] == epoch_stop:
                        break
                else:
                    if data_append[0]['time'] == epoch_stop:
                        break
                time.sleep(.5)
                tries += 1
                if tries > 5:
                    # Admit failure and return
                    warnings.warn("Exchange failed to provide updated data within the timeout.")
                    return self.cast_type(response, return_as)
                try:
                    data_append = [self.get_product_history(symbol,
                                                            epoch_stop - resolution_seconds,
                                                            epoch_stop,
                                                            resolution_seconds).iloc[-1].to_dict()]
                    data_append[0]['time'] = int(data_append[0]['time'])
                except IndexError:
                    # If there is no recent data on the exchange this will be an empty dataframe.
                    # This happens for low volume
                    utils.info_print("Most recent bar at this resolution does not yet exist - skipping.")
                    break

            response = response.append(data_append, ignore_index=True)

        return self.cast_type(response, return_as)

    def overridden_history(self, symbol, epoch_start, epoch_stop, resolution, **kwargs) -> pd.DataFrame:
        return self.get_product_history(symbol, epoch_start, epoch_stop, resolution)

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

    @staticmethod
    def cast_type(response: pd.DataFrame, return_as: str):
        if return_as != 'df' and return_as != 'deque':
            return response.to_dict(return_as)
        elif return_as == 'deque':
            # Create a deque object that has the same length
            response = response.to_dict('list')
            for i in response.keys():
                response[i] = deque(response[i], len(response[i]))
            return response
        return response

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

    @abc.abstractmethod
    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        pass

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
