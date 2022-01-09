"""
    Object for cleanly storing & printing complex backtest results.
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

from pandas import DataFrame
from blankly.utils.utils import time_interval_to_seconds as _time_interval_to_seconds


class BacktestResult:
    def __init__(self, history_and_returns: dict, trades: dict, history: dict,
                 start_time: float, stop_time: float, quote_currency: str, price_events: list):
        # This can use a ton of memory if these attributes are not cleared
        self.history_and_returns = history_and_returns
        self.metrics = None  # Assigned after construction
        self.user_callbacks = None  # Assigned after construction
        self.trades = trades
        self.history = history

        self.quote_currency = quote_currency
        self.price_events = price_events

        self.start_time = start_time
        self.stop_time = stop_time

    def get_account_history(self) -> DataFrame:
        return self.history_and_returns['history']

    def get_returns(self) -> DataFrame:
        return self.history_and_returns['returns']

    def get_resampled_account(self) -> DataFrame:
        return self.history_and_returns['resampled_account_value']

    def get_user_callback_results(self) -> dict:
        return self.user_callbacks

    def get_metrics(self) -> dict:
        return self.metrics

    def resample_account(self, symbol, interval: [str, float],
                         use_asset_history: bool = False,
                         use_price=None) -> DataFrame:
        """
        Resample the raw account value metrics to any resolution

        Args:
            symbol: The column to resample at the interval resolution. This can include the account value column
            interval: A string such as '1h' or '1m' or a number in seconds such as 3600 or 60 which the values
            will be resampled at
            use_asset_history: Use the history from the assets rather than the account history
            use_price: Specify a price to use when querying comparison columns
        """
        search_index = 0

        def search_price(values, times, epoch):
            # In this case because each asset is called individually
            def search(arr, size, x):
                # Use a global search index to accelerate search
                nonlocal search_index

                while True:
                    if search_index == size:
                        # Must be the last one in the list
                        return search_index - 1

                    if arr[search_index] <= x <= arr[search_index + 1]:
                        # Found it in this range
                        return search_index
                    else:
                        search_index += 1
            try:
                # Iterate and find the correct quote price
                index_ = search(times, len(times), epoch)
                return values[index_]
            except KeyError:
                # Not a currency that we have data for at all
                return 0

        resampled_array = []
        interval = _time_interval_to_seconds(interval)

        if use_asset_history:
            # Find the necessary values to assemble the resamples
            time_array = self.history[symbol]['time'].tolist()
            price_array = self.history[symbol][use_price].tolist()
        else:
            # Find the necessary values to assemble the resamples
            time_array = self.history_and_returns['history']['time'].tolist()
            price_array = self.history_and_returns['history'][symbol].tolist()

        # Add the epoch
        epoch_start = time_array[0]
        epoch_stop = time_array[-1]

        while epoch_start <= epoch_stop:
            # Append this dict to the array
            resampled_array.append({
                'time': epoch_start,
                'value': search_price(price_array, time_array, epoch_start)
            })

            # Increase the epoch value
            epoch_start += interval

        # Turn that resample into a dataframe
        df_conversion = DataFrame(columns=['time', 'value'])
        return df_conversion.append(resampled_array, ignore_index=True)

    def __str__(self):
        return_string = "\n"
        return_string += "Historical Dataframes: \n"

        return_string += "Account History: \n"
        return_string += self.history_and_returns['history'].__str__()
        return_string += "\n"

        return_string += "Account Returns: \n"
        return_string += self.history_and_returns['returns'].__str__()
        return_string += "\n"

        return_string += "Resampled Account Value: \n"
        return_string += self.history_and_returns['resampled_account_value'].__str__()
        return_string += "\n"

        return_string += "Blankly Metrics: \n"
        for i in self.metrics.keys():
            spaces_needed = 33 - len(i)
            user_metrics_line = i + ": " + (' ' * spaces_needed) + str(self.metrics[i])
            if i[-3:] == "(%)":
                user_metrics_line += "%"
            user_metrics_line += "\n"
            return_string += user_metrics_line

        if self.user_callbacks != {}:
            return_string += "\n"
            return_string += "User Callbacks: \n"
            for i in self.user_callbacks.keys():
                return_string += i + ": " + str(self.user_callbacks[i]) + "\n"

        return return_string
