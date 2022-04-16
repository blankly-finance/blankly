"""
    Base ExchangeInterface object.
    Copyright (C) 2022 Matias Kotlik

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
from collections import deque
from datetime import datetime as dt
from typing import Union

import numpy
import pandas
import pandas as pd
from dateutil import parser

from blankly import utils
from blankly.utils import time_interval_to_seconds


# A lot of this class is just glue between ExchangeInterface and the new Futures classes.
# At some point it should probably all be refactored away but for now let's get futures working!
class ABCBaseExchangeInterface(abc.ABC):

    @abc.abstractmethod
    def get_exchange_type(self):
        pass

    @abc.abstractmethod
    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        pass

    def history(self,
                symbol: str,
                to: Union[str, int] = 200,
                resolution: Union[str, float] = '1d',
                start_date: Union[str, dt, float] = None,
                end_date: Union[str, dt, float] = None,
                return_as: str = 'df'):

        start, stop, res_seconds, to, present = self.calculate_epochs(start_date, end_date, resolution, to)

        response = self.overridden_history(symbol, start, stop, res_seconds, to=to,)

        # Add a check to make sure that coinbase pro has updated
        # I tried to delete this code but the entire function broke :(
        if present and self.get_exchange_type() == "coinbase_pro":
            data_append = None
            tries = 0
            while True:
                if data_append is None:
                    # We can continue if this is valid
                    if response['time'].iloc[-1] == stop:
                        break
                else:
                    if data_append[0]['time'] == stop:
                        break
                time.sleep(.5)
                tries += 1
                if tries > 5:
                    # Admit failure and return
                    warnings.warn("Exchange failed to provide updated data within the timeout.")
                    return self.cast_type(response, return_as)
                try:
                    data_append = [self.get_product_history(symbol,
                                                            stop - res_seconds,
                                                            stop,
                                                            res_seconds).iloc[-1].to_dict()]
                    data_append[0]['time'] = int(data_append[0]['time'])
                except IndexError:
                    # If there is no recent data on the exchange this will be an empty dataframe.
                    # This happens for low volume
                    utils.info_print("Most recent bar at this resolution does not yet exist - skipping.")
                    break

            response = response.append(data_append, ignore_index=True)

        # Determine the deque length - we really should use this generally
        if isinstance(to, int):
            point_count = to
        else:
            point_count = (stop-start)/res_seconds + 1
        # response.index = pd.to_datetime(response['time'], unit='s')
        return self.cast_type(response, return_as, point_count)

    def calculate_epochs(self, start_date, end_date, resolution, to):
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
            # Binance is nice enough to update OHLCV data, so we have to exclude that by subtracting a resolution
            epoch_stop = most_recent_valid_resolution - resolution_seconds
            count_from = most_recent_valid_resolution
        else:
            if isinstance(end_date, str):
                parsed_date = parser.parse(end_date)
            elif isinstance(end_date, float) or isinstance(end_date, numpy.int64) or isinstance(end_date, int) or \
                    isinstance(end_date, numpy.int32):
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
        return epoch_start, epoch_stop, resolution_seconds, to, to_present

    def overridden_history(self, symbol, epoch_start, epoch_stop, resolution, **kwargs) -> pd.DataFrame:
        return self.get_product_history(symbol, epoch_start, epoch_stop, resolution)

    def is_backtesting(self):
        return None

    @staticmethod
    def cast_type(response: pd.DataFrame, return_as: str, point_count=None):
        if return_as != 'df' and return_as != 'deque':
            return response.to_dict(return_as)
        elif return_as == 'deque':
            # Create a deque object that has the same length
            response = response.to_dict('list')
            for i in response.keys():
                response[i] = deque(response[i], point_count)
            return response
        elif return_as == 'df':
            return response
        else:
            utils.info_print(f"Return type {return_as} is not supported.")
        return response
