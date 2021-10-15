"""
    Backtesting controller for paper trading interface
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

import os
import traceback
import typing
from datetime import datetime as dt

import pandas as pd
from bokeh.layouts import column as bokeh_columns
from bokeh.models import HoverTool
from bokeh.palettes import Category10_10
from bokeh.plotting import ColumnDataSource, figure, show

import blankly.exchanges.interfaces.paper_trade.metrics as metrics
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.exchanges.interfaces.paper_trade.paper_trade import PaperTrade
from blankly.exchanges.interfaces.paper_trade.paper_trade_interface import PaperTradeInterface
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import load_backtest_preferences, update_progress, write_backtest_preferences, \
    get_base_asset, get_quote_asset


def to_string_key(separated_list):
    output = ""
    for i in range(len(separated_list) - 1):
        output += str(separated_list[i])
        output += ","
    output += str(separated_list[-1:][0])
    return output


def split(base_range, local_segments) -> typing.Tuple[list, list]:
    """
    Find the negative given from a range and a set of other ranges

    Args:
        base_range: Backing array containing a range such as [1, 10]
        local_segments: An array of segments that we have such as [-5, 5], [6,7]
    Returns:
        The output of the example inputs above would be [[8, 10]]
    """

    # If we don't have any local segments there is no need for any of this, just download the whole set
    used_ranges = []
    positive_ranges = []  # These are the ranges that we have downloaded
    negative_ranges = []  # These are the ranges that we need

    def intersection(as_, ae, bs, be):
        """
        Find the intersection of two ranges
        Implementation from https://scicomp.stackexchange.com/a/26260

        Args:
            as_: Low of first range
            ae: High of first range
            bs: Low of second range
            be: High of second range
        """
        if bs > ae or as_ > be:
            return None
        else:
            os_ = max(as_, bs)
            oe = min(ae, be)
            return [os_, oe]
    for i in local_segments:
        intersection_range = intersection(base_range[0], base_range[1], i[0], i[1])
        if intersection_range is None:
            continue
        # We now know every single downloaded range that we need to keep
        used_ranges.append(i)

        # Now these are all intersections that we will filter to find the negative ranges to download
        positive_ranges.append(intersection_range)

    # Create a list of indexes that need to be pushed into a single list, arrays like  [1, 5] and [3, 7] would need to
    #  become [1, 7]

    # First we have to sort the lists to have the same starting value
    positive_ranges = sorted(positive_ranges, key=lambda x: x[0])

    aggregate_indexes = []
    for i in range(len(positive_ranges) - 1):
        intersection_range = intersection(positive_ranges[i][0], positive_ranges[i][1],
                                          positive_ranges[i + 1][0],     positive_ranges[i + 1][1])
        if intersection_range is not None:
            aggregate_indexes.append([i, i + 1])

    # Now aggregate from the last result
    for i in aggregate_indexes:
        # Pull the lower bound right out of the lower index from the aggregate_indexes approach
        lower_bound = positive_ranges[i[0]][0]

        positive_ranges[i[0]] = None

        # Push that same lower bound into the array that was above it
        positive_ranges[i[1]][0] = lower_bound

    # Filter out the None's that were added
    positive_ranges = [x for x in positive_ranges if not (x is None)]

    # Now just try to find the gaps in the positive ranges and those are our negative ranges
    for i in range(len(positive_ranges) - 1):
        negative_ranges.append([positive_ranges[i][1], positive_ranges[i+1][0]])

    try:
        # Now we just have to make sure to check the bounds
        # If the very first value we have is greater than what we requested
        if positive_ranges[0][0] > base_range[0]:
            # We then need the base range up to our first positive value
            negative_ranges.append([base_range[0], positive_ranges[0][0]])

        # If the last positive range is less than our requested final
        if positive_ranges[-1][1] < base_range[1]:
            # The actual value is from the last positive range value to our requested final value
            negative_ranges.append([positive_ranges[-1][1], base_range[1]])
    except IndexError:
        return [], [base_range]

    return used_ranges, negative_ranges


class BackTestController:
    def __init__(self, paper_trade_exchange: PaperTrade, backtest_settings_path: str = None, callbacks: list = None):
        self.preferences = load_backtest_preferences(backtest_settings_path)
        self.backtest_settings_path = backtest_settings_path
        if not paper_trade_exchange.get_type() == "paper_trade":
            raise ValueError("Backtest controller was not constructed with a paper trade exchange object.")
        self.interface: PaperTradeInterface = paper_trade_exchange.get_interface()

        self.price_events = []

        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks

        self.current_time = None
        self.initial_time = None

        self.prices = []  # [epoch, "BTC-USD", price]

        self.price_dictionary = {}

        self.pd_prices = None

        # User added times
        self.__user_added_times = []

        self.use_price = None

        self.queue_backtest_write = False

        self.quote_currency = self.preferences['settings']['quote_account_value_in']

        # Create a global generator because a second yield function gets really nasty
        self.__color_generator = Category10_10.__iter__()

        self.initial_account = None

        self.__exchange_type = self.interface.get_exchange_type()

        # Create our own traded assets dictionary because we customize it a bit
        self.__traded_assets = []

        # Because the times are run in order we can use this variable to optimize account value searching
        self.__current_search_index = 0

        # Export a time for use in other classes
        self.time = None

    def sync_prices(self) -> dict:
        cache_folder = self.preferences['settings']["cache_location"]
        # Make sure the cache folder exists and read files
        try:
            files = os.listdir(cache_folder)
        except FileNotFoundError:
            files = []
            os.mkdir(cache_folder)

        available_files = []
        for i in range(len(files)):
            # example file name: 'BTC-USD.1622400000.1622510793.60.csv'
            # Remove the .csv from each of the files: BTC-USD.1622400000.1622510793.60
            identifier = files[i][:-4].split(",")
            identifier[1] = int(identifier[1])
            identifier[2] = int(identifier[2])
            identifier[3] = int(identifier[3])
            available_files.append(identifier)

        # This is only the downloaded data
        local_history_blocks = {}
        for i in available_files:
            # Sort these into resolutions
            asset = i[0]

            # Make sure to add the asset as a key
            if asset not in list(local_history_blocks.keys()):
                local_history_blocks[asset] = {}

            # Add each resolution to its own internal list
            if i[3] not in list(local_history_blocks[asset].keys()):
                local_history_blocks[asset][i[3]] = [i]
            else:
                local_history_blocks[asset][i[3]].append(i)

        # def segment(conjoined_ranges: list) -> list:
        #     """
        #     Split a list with sets of even intervals into multiple lists. The list must be single increments in all
        #     places except for the splits
        #     """
        #     ranges = []
        #     segments = 0
        #     for i in range(len(conjoined_ranges)-1):
        #         i += 1
        #         if conjoined_ranges[i] - conjoined_ranges[i-1] != 1:
        #             segmented_list = conjoined_ranges[segments:i]
        #
        #             ranges.append((segmented_list[0], segmented_list[-1]))
        #             segments = i + 1
        #
        #     return ranges

        # This is the data the user has requested: [asset_id, start_time, end_time, resolution]
        final_prices = {}
        for i in range(len(self.__user_added_times)):
            if self.__user_added_times[i] is None:
                continue
            asset = self.__user_added_times[i][0]
            resolution = self.__user_added_times[i][3]
            start_time = self.__user_added_times[i][1]
            end_time = self.__user_added_times[i][2] - resolution

            if end_time < start_time:
                raise RuntimeError("Must specify  a longer timeframe to run the backtest.")

            download_ranges = []

            # Attempt to find the same symbol/asset possibilities in the backtest blocks
            try:
                download_ranges = local_history_blocks[asset][resolution]
            except KeyError:
                pass

            for j in range(len(download_ranges)):
                download_ranges[j] = download_ranges[j][1:3]

            used_ranges, negative_ranges = split([start_time, end_time], download_ranges)

            # for j in download_ranges:
            #     download_start_time = j[1]
            #     download_end_time = j[2] - resolution
            #
            #     contains_start = False
            #     contains_end = False
            #     if download_start_time <= start_time <= download_end_time:
            #         contains_start = True
            #     elif download_start_time <= end_time <= download_end_time:
            #         contains_end = True
            #
            #     if contains_start or contains_end:
            #         # Read in the whole thing if it has any sort of relevance on the data
            #         relevant_df = pd.read_csv(os.path.join(cache_folder,
            #                                                to_string_key(j) + ".csv"))
            #
            #         # If it only contains the start then it must be offset too high or is too long
            #         if contains_start and not contains_end:
            #             relevant_df = relevant_df[relevant_df['time'] >= start_time]
            #
            #             # Set the end time to match the first time in the relevant dataframe
            #             self.__user_added_times[i][1] = relevant_df['time'].iloc[-1]
            #
            #         # If it only contains the end then it must be offset too low or is too short
            #         if contains_end and not contains_start:
            #             relevant_df = relevant_df[relevant_df['time'] <= end_time]
            #
            #             # Set the start time to match the very last time of the relevant dataframe
            #             self.__user_added_times[i][2] = relevant_df['time'].iloc[0]
            #
            #         # If it contains start and end then it's just right
            #         if contains_end and contains_start:
            #             relevant_df = relevant_df[relevant_df['time'] >= start_time]
            #             relevant_df = relevant_df[relevant_df['time'] <= end_time]
            #
            #             # This dataset has been completed so there is no need to continue
            #             self.__user_added_times[i] = None
            #
            #         # Write these into the data array
            #         if asset not in list(final_prices.keys()):
            #             final_prices[asset] = relevant_df
            #         else:
            #             final_prices[asset] = pd.concat([final_prices[asset], relevant_df])

            relevant_data = []
            for j in used_ranges:
                relevant_data.append(pd.read_csv(os.path.join(cache_folder, to_string_key([asset, j[0], j[1],
                                                                                           resolution]) + ".csv")))

            if len(relevant_data) > 0:
                final_prices[asset] = pd.concat(relevant_data)

            # If there is any data left to download do it here
            for j in negative_ranges:
                print("No cached data found for " + asset + " from: " + str(j[0]) + " to " +
                      str(j[1]) + " at a resolution of " + str(resolution) + " seconds.")
                download = self.interface.get_product_history(asset,
                                                              j[0],
                                                              j[1],
                                                              resolution)

                # Write the file but this time include very accurately the start and end times
                if self.preferences['settings']['continuous_caching']:
                    download.to_csv(os.path.join(cache_folder, f'{asset},'
                                                               f'{j[0]},'
                                                               f'{j[1]+resolution},'  # This adds resolution back to the
                                                                                      #  exported time series
                                                               f'{resolution}.csv'),
                                    index=False)

                # Write these into the data array
                if asset not in list(final_prices.keys()):
                    final_prices[asset] = download
                else:
                    final_prices[asset] = pd.concat([final_prices[asset], download])

            # After all the negative ranges are appended, we need to sort & trim
            final_prices[asset] = final_prices[asset].sort_values(by=['time'], ignore_index=True)

            # Now make sure to just trim our times to hit the start and end times
            final_prices[asset] = final_prices[asset][final_prices[asset]['time'] >= start_time]
            final_prices[asset] = final_prices[asset][final_prices[asset]['time'] <= end_time + resolution]  # Add back

        return final_prices

        # cache_folder = self.preferences['settings']["cache_location"]
        # # Make sure the cache folder exists and read files
        # try:
        #     files = os.listdir(cache_folder)
        # except FileNotFoundError:
        #     files = []
        #     os.mkdir(cache_folder)
        #
        # available_files = []
        # for i in range(len(files)):
        #     # example file name: 'BTC-USD.1622400000.1622510793.60.csv'
        #     # Remove the .csv from each of the files: BTC-USD.1622400000.1622510793.60
        #     identifier = files[i][:-4].split(",")
        #     identifier[1] = float(identifier[1])
        #     identifier[2] = float(identifier[2])
        #     identifier[3] = float(identifier[3])
        #     available_files.append(identifier)
        #
        # assets = self.preferences['price_data']['assets']  # type: dict
        # for i in assets:
        #     identifier = [i[0], i[1], i[2], i[3]]
        #     string_identifier = to_string_key(identifier)
        #     if identifier in available_files:
        #         # Read the csv here
        #         if tuple(identifier) not in self.price_dictionary.keys():
        #             print("Including: " + string_identifier + ".csv in backtest.")
        #             self.price_dictionary[tuple(identifier)] = pd.read_csv(os.path.join(cache_folder,
        #                                                                                 string_identifier + ".csv")
        #                                                                    )
        #     else:
        #         if tuple(identifier) not in self.price_dictionary.keys():
        #             print("No exact cache exists for " + str(identifier[0]) + " from " + str(identifier[1]) + " to " +
        #                   str(identifier[2]) + " at " + str(identifier[3]) + "s resolution. Downloading...")
        #             download = self.interface.get_product_history(identifier[0], identifier[1], identifier[2],
        #                                                           identifier[3])
        #             self.price_dictionary[tuple(identifier)] = download
        #             if save:
        #                 download.to_csv(os.path.join(cache_folder, string_identifier + ".csv"), index=False)
        #
        # # Merge all the same asset ids into the same dictionary spots
        # unique_assets = {}
        # for k, v in self.price_dictionary.items():
        #     if k[0] in unique_assets:
        #         unique_assets[k[0]] = pd.concat([unique_assets[k[0]], v], ignore_index=True)
        #     else:
        #         unique_assets[k[0]] = v
        #
        # return unique_assets

    def add_prices(self, asset_id, start_time, end_time, resolution, save=False):
        # Create its unique identifier
        identifier = [asset_id, int(start_time), int(end_time), int(resolution)]

        # If it's not loaded then write it to the file
        if tuple(identifier) not in self.price_dictionary.keys():
            # self.preferences['price_data']['assets'].append(identifier)
            self.__user_added_times.append(identifier)
            if save:
                self.queue_backtest_write = True
        else:
            print("already identified")

    def append_backtest_price_event(self, callback: typing.Callable, asset_id, time_interval, state_object, ohlc, init,
                                    teardown):
        if isinstance(time_interval, str):
            time_interval = time_interval_to_seconds(time_interval)
        self.price_events.append([callback, asset_id, time_interval, state_object, ohlc, init, teardown])

    def write_setting(self, key, value, save=False):
        """
        Write a setting to the .json preferences

        Args:
            key: Key under settings
            value: Value to set that settings key to
            save: Write this new setting to the file
        """
        self.preferences['settings'][key] = value
        if save:
            self.queue_backtest_write = True

    def write_initial_price_values(self, account_dictionary):
        """
        Write in a new price dictionary for the paper trade exchange.
        """
        self.interface.override_local_account(account_dictionary)

    def format_account_data(self, local_time) -> typing.Tuple[typing.Dict[typing.Union[str, typing.Any],
                                                                          typing.Union[int, typing.Any]],
                                                              typing.Dict[typing.Union[str, typing.Any],
                                                                          typing.Union[int, typing.Any]]]:

        # This is done so that only traded assets are evaluated.
        true_available = {}
        assets = self.__traded_assets
        true_account = {}
        for i in assets:
            # Grab the account status
            true_account[i] = self.interface.get_account(i)

        # Create an account total value
        value_total = 0

        no_trade_available = {}
        # No trade account total
        no_trade_value = 0

        # Save this up front so that it can be removed from the price calculation (its always a value of 1 anyway)
        quote_value = true_account[self.quote_currency]['available'] + true_account[self.quote_currency]['hold']
        try:
            del true_account[self.quote_currency]
        except KeyError:
            pass

        for i in list(true_account.keys()):
            # Funds on hold are still added
            true_available[i] = true_account[i]['available'] + true_account[i]['hold']
            no_trade_available[i] = self.initial_account[i]['available'] + self.initial_account[i]['hold']
            currency_pair = i

            # Convert to quote (this could be optimized a bit)
            if self.__exchange_type != 'alpaca':
                currency_pair += '-'
                currency_pair += self.quote_currency

            # Get price at time
            try:
                price = self.interface.get_price(currency_pair)
            except KeyError:
                # Must be a currency we have no data for
                price = 0
            value_total += price * true_available[i]
            no_trade_value += price * no_trade_available[i]

        # Make sure to add the time key in
        true_available['time'] = local_time
        no_trade_available['time'] = local_time

        value_total += quote_value
        true_available[self.quote_currency] = quote_value

        no_trade_value += self.initial_account[self.quote_currency]['available'] + \
                          self.initial_account[self.quote_currency]['hold']

        true_available['Account Value (' + self.quote_currency + ')'] = value_total

        no_trade_available['Account Value (No Trades)'] = no_trade_value

        return true_available, no_trade_available

    def __account_was_used(self, column) -> bool:
        show_zero_delta = self.preferences['settings']['show_tickers_with_zero_delta']

        # Just check if its in the traded assets or if the zero delta is enabled
        used = self.__traded_assets
        is_used = column in used or 'Account Value (' + self.quote_currency + ')' == column

        # Return true if they are not the same or the setting is set to true
        output = is_used or show_zero_delta
        return output

    def __next_color(self):
        # This should be a generator but it doesn't work without doing a foreach loop
        try:
            return next(self.__color_generator)
        except StopIteration:
            self.__color_generator = Category10_10.__iter__()
            return next(self.__color_generator)

    def run(self) -> BacktestResult:
        """
        Setup
        """

        # Create this initial so that we can compare how our strategy performs
        self.initial_account = self.interface.get_account()

        # Write our queued edits to the file
        if self.queue_backtest_write:
            write_backtest_preferences(self.preferences, self.backtest_settings_path)

        prices = self.sync_prices()

        # Organize each price into this structure: [epoch, "BTC-USD", price, open, high, low, close, volume]
        use_price = self.preferences['settings']['use_price']
        self.use_price = use_price

        self.pd_prices = {**prices}

        for k, v in prices.items():
            frame = v  # type: pd.DataFrame

            # Be sure to push these initial prices to the strategy
            self.interface.receive_price(k, v[use_price].iloc[0])

            for index, row in frame.iterrows():
                # TODO iterrows() is allegedly pretty slow
                self.prices.append([row.time, k, row[use_price],
                                    row['open'],  # (index) 3
                                    row['high'],  # 4
                                    row['low'],  # 5
                                    row['close'],  # 6
                                    row['volume']])  # 7

        # pushing these prices together makes the time go weird
        self.prices = sorted(self.prices)

        try:
            self.current_time = self.prices[0][0]
        except IndexError:
            raise IndexError('No cached or downloaded data available. Try adding arguments such as to="1y" '
                             'in the backtest command.')
        self.initial_time = self.current_time

        # Add a section to the price events which controls the next time they run & change to array of dicts
        for i in range(len(self.price_events)):
            self.price_events[i] = {
                'function': self.price_events[i][0],
                'asset_id': self.price_events[i][1],
                'interval': self.price_events[i][2],
                'state_object': self.price_events[i][3],
                'next_run': self.initial_time,
                'ohlc': self.price_events[i][4],
                'init': self.price_events[i][5],
                'teardown': self.price_events[i][6]
            }

        if prices == {} or self.price_events == []:
            raise ValueError("Either no price data or backtest events given. "
                             "Use .append_backtest_price_data or "
                             "append_backtest_price_event to create the backtest model.")

        # Initialize this before the callbacks so it works in the initialization functions
        self.time = self.initial_time

        # Run the initialization functions for the price events
        print("\nInitializing...")
        for i in self.price_events:
            if i['init'] is not None:
                i['init'](i['asset_id'], i['state_object'])

        """
        Begin backtesting
        """

        self.interface.set_backtesting(True)

        # Re-evaluate the traded assets account
        # This is mainly used if the user has an account with some value that gets added in at the backtest point
        # This occurs after initialization so there has to be a function to test & re-evaluate that
        self.interface.evaluate_traded_account_assets()
        column_keys = list.copy(self.interface.traded_assets)

        # Comically if you don't include the quote at any point there will be an error
        if self.quote_currency not in column_keys:
            column_keys.append(self.quote_currency)
        # If they start a price event on something they don't own, this should also be included
        for i in self.price_events:
            base_asset = get_base_asset(i['asset_id'])
            quote_asset = get_quote_asset(i['asset_id'])
            if base_asset not in column_keys:
                column_keys.append(base_asset)
            if quote_asset not in column_keys:
                column_keys.append(quote_asset)
        self.__traded_assets = list.copy(column_keys)
        column_keys.append('time')

        # column_keys = ['time']
        # for i in account.keys():
        #     column_keys.append(i['currency'])

        cycle_status = pd.DataFrame(columns=column_keys)

        no_trade_cycle_status = pd.DataFrame(columns=column_keys)

        # Append dictionaries to this to make the pandas dataframe
        price_data = []

        # Append dictionaries to this to make the no trade dataframe
        no_trade = []

        # Add an initial account row here
        if self.preferences['settings']['save_initial_account_value']:
            available_dict, no_trade_dict = self.format_account_data(self.initial_time)
            price_data.append(available_dict)
            no_trade.append(no_trade_dict)

        show_progress = self.preferences['settings']['show_progress_during_backtest']

        ignore_exceptions = self.preferences['settings']['ignore_user_exceptions']

        print("\nBacktesting...")
        price_number = len(self.prices)
        try:
            for i in range(price_number):
                price_array = self.prices[i]
                if show_progress:
                    if i % 100 == 0:
                        update_progress(i / price_number)
                self.interface.receive_price(price_array[1], price_array[2])
                self.current_time = price_array[0]
                self.interface.evaluate_limits()

                while True:
                    # Need to go through and establish an order for each of the price events
                    self.price_events = sorted(self.price_events, key=lambda sort_key: sort_key['next_run'])

                    # Now the lowest one has to go past the current time to be invalid
                    if self.price_events[0]['next_run'] > self.current_time:
                        break

                    local_time = self.price_events[0]['next_run']

                    # Export the time for strategy
                    self.time = local_time

                    self.interface.receive_time(local_time)

                    # This is the actual callback to the user space
                    try:
                        if self.price_events[0]['ohlc']:
                            # This pulls all the price data out of the price array defined on line 260
                            self.price_events[0]['function']({'open': price_array[3],
                                                              'high': price_array[4],
                                                              'low': price_array[5],
                                                              'close': price_array[6],
                                                              'volume': price_array[7]},

                                                             self.price_events[0]['asset_id'],
                                                             self.price_events[0]['state_object'])
                        else:
                            self.price_events[0]['function'](self.interface.get_price(self.price_events[0]['asset_id']),
                                                             self.price_events[0]['asset_id'], self.price_events[0][
                                                                 'state_object'])
                    except Exception as e:
                        if ignore_exceptions:
                            traceback.print_exc()
                        else:
                            raise e

                    # Delay the next run until after the interval
                    self.price_events[0]['next_run'] += self.price_events[0]['interval']

                    available_dict, no_trade_dict = self.format_account_data(local_time)

                    price_data.append(available_dict)

                    no_trade.append(no_trade_dict)

            # Finally run the teardown functions
            for i in self.price_events:
                # Pull the teardown and pass the state object
                if callable(i['teardown']):
                    i['teardown'](i['state_object'])
        except Exception:
            traceback.print_exc()

        # Reset time to be None to indicate we're no longer in a backtest
        self.time = None

        # Push the accounts to the dataframe
        cycle_status = cycle_status.append(price_data, ignore_index=True).sort_values(by=['time'])

        if len(cycle_status) == 0:
            raise RuntimeError("Empty result - no valid backtesting events occurred. Was there an error?.")

        no_trade_cycle_status = no_trade_cycle_status.append(no_trade, ignore_index=True).sort_values(by=['time'])

        figures = []
        # for i in self.prices:
        #     result_index = cycle_status['time'].sub(i[0]).abs().idxmin()
        #     for i in cycle_status.iloc[result_index]:

        hover = HoverTool(
            tooltips=[
                ('value', '@value')
            ],

            # formatters={
            #     'time': 'datetime',  # use 'datetime' formatter for 'date' field
            #     '@{value}': 'printf',   # use 'printf' formatter for '@{adj close}' field
            # },

            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode='vline'
        )

        # Back up the epoch list so that it can be used later for re-sampling
        epoch_backup = cycle_status['time'].tolist()

        if self.preferences['settings']['GUI_output']:
            global_x_range = None

            time = [dt.fromtimestamp(ts) for ts in cycle_status['time']]

            for column in cycle_status:
                if column != 'time' and self.__account_was_used(column):
                    p = figure(plot_width=900, plot_height=200, x_axis_type='datetime')
                    source = ColumnDataSource(data=dict(
                        time=time,
                        value=cycle_status[column].tolist()
                    ))
                    p.step('time', 'value',
                           source=source,
                           line_width=2,
                           color=self.__next_color(),
                           legend_label=column,
                           mode="after",
                           )

                    # Replica of whats above to add the no-trade line to the backtest
                    if column == 'Account Value (' + self.quote_currency + ')':
                        source = ColumnDataSource(data=dict(
                            time=time,
                            value=no_trade_cycle_status['Account Value (No Trades)'].tolist()
                        ))
                        p.step('time', 'value',
                               source=source,
                               line_width=2,
                               color=self.__next_color(),
                               legend_label='Account Value (No Trades)',
                               mode="after")

                    p.add_tools(hover)

                    # Format graph
                    p.legend.location = "top_left"
                    p.legend.title = column
                    p.legend.title_text_font_style = "bold"
                    p.legend.title_text_font_size = "20px"
                    if global_x_range is None:
                        global_x_range = p.x_range
                    else:
                        p.x_range = global_x_range

                    figures.append(p)

            show(bokeh_columns(figures))

        def is_number(s):
            try:
                float(s)
                # Love how bools cast to a number
                return not isinstance(s, bool)
            except ValueError:
                return False

        dataframes = {
            'history': cycle_status
        }
        metrics_indicators = {}
        user_callbacks = {}

        # Check if it needs resampling
        resample_setting = self.preferences['settings']['resample_account_value_for_metrics']
        if isinstance(resample_setting, str) or is_number(resample_setting):
            # Backing arrays. We can't append directly to the dataframe so array has to also be made

            def search_price(asset_id, epoch):
                # In this case because each asset is called individually
                def search(arr, size, x):
                    while True:
                        if self.__current_search_index == size:
                            # Must be the last one in the list
                            return self.__current_search_index - 1

                        if arr[self.__current_search_index] <= x <= arr[self.__current_search_index + 1]:
                            # Found it in this range
                            return self.__current_search_index
                        else:
                            self.__current_search_index += 1
                try:
                    prices_ = self.pd_prices[asset_id][self.use_price]  # type: pd.Series
                    times = self.pd_prices[asset_id]['time']  # type: pd.Series

                    # Iterate and find the correct quote price
                    index_ = search(times, times.size, epoch)
                    # print('Found price for', asset_id, prices[index])
                    return prices_[index_]
                except KeyError:
                    # Not a currency that we have data for at all
                    return 0

            resampled_returns = pd.DataFrame(columns=['time', 'value'])
            resampled_backing_array = []

            # Find the interval second value
            interval_value = time_interval_to_seconds(resample_setting)

            # Assign start and stop limits
            epoch_start = epoch_backup[0]
            epoch_max = epoch_backup[len(epoch_backup) - 1]

            # Reset the current search index to zero for re-searching
            self.__current_search_index = 0
            # Going to push this in as a single column version of our price data so that __determine_price can handle it
            self.pd_prices['Account Value (' + self.quote_currency + ')'] = pd.DataFrame()
            self.pd_prices['Account Value (' + self.quote_currency + ')'][use_price] = \
                cycle_status['Account Value (' + self.quote_currency + ')']

            self.pd_prices['Account Value (' + self.quote_currency + ')']['time'] = cycle_status['time']

            while epoch_start <= epoch_max:
                # Append this dict to the array
                resampled_backing_array.append({
                    'time': epoch_start,
                    'value': search_price('Account Value (' + self.quote_currency + ')', epoch_start)
                })

                # Increase the epoch value
                epoch_start += interval_value

            # Put this in the dataframe
            resampled_returns = resampled_returns.append(resampled_backing_array, ignore_index=True)

            # This is the resampled version
            dataframes['resampled_account_value'] = resampled_returns

            # Now we need to copy it and find the differences
            returns = resampled_returns.copy(deep=True)

            # Default diff parameters should do it
            returns['value'] = returns['value'].diff()

            # Now write it to our dictionary
            dataframes['returns'] = returns

            # -----=====*****=====----- I thought I stopped doing these comments when I actually learned to code
            metrics_indicators['cagr'] = metrics.cagr(dataframes)
            try:
                metrics_indicators['cum_returns'] = metrics.cum_returns(dataframes)
            except ZeroDivisionError:
                raise ZeroDivisionError("Division by zero when calculating cum returns. "
                                        "Are there valid account datapoints?")

            def attempt(math_callable: typing.Callable, dict_of_dataframes: dict):
                try:
                    return math_callable(dict_of_dataframes)
                except ZeroDivisionError:
                    return 'failed'
            metrics_indicators['sortino'] = attempt(metrics.sortino, dataframes)
            metrics_indicators['sharpe'] = attempt(metrics.sharpe, dataframes)
            metrics_indicators['calmar'] = attempt(metrics.calmar, dataframes)
            metrics_indicators['volatility'] = attempt(metrics.volatility, dataframes)
            metrics_indicators['variance'] = attempt(metrics.variance, dataframes)
            metrics_indicators['var'] = attempt(metrics.var, dataframes)
            metrics_indicators['cvar'] = attempt(metrics.cvar, dataframes)
            metrics_indicators['max_drawdown'] = attempt(metrics.max_drawdown, dataframes)
            # metrics_indicators['beta'] = attempt(metrics.beta, dataframes)
            # -----=====*****=====-----

        # Run this last so that the user can override what they want
        for callback in self.callbacks:
            user_callbacks[callback.__name__] = callback(dataframes)

        result_object = BacktestResult(dataframes, metrics_indicators, user_callbacks)

        self.interface.set_backtesting(False)
        return result_object
