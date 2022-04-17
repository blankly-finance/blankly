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
import json
import os
import time
import traceback
import typing
from datetime import datetime as dt
import copy
import enum
import blankly

import numpy as np
import pandas as pd
import requests
from bokeh.layouts import column as bokeh_columns
from bokeh.models import HoverTool
from bokeh.palettes import Category10_10
from bokeh.plotting import ColumnDataSource, figure, show

import blankly.exchanges.interfaces.paper_trade.metrics as metrics
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.exchanges.interfaces.paper_trade.paper_trade_interface import PaperTradeInterface
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import load_backtest_preferences, write_backtest_preferences, info_print, update_progress, \
    get_base_asset, get_quote_asset
from blankly.exchanges.interfaces.paper_trade.backtest.format_platform_result import \
    format_platform_result

from blankly.exchanges.interfaces.paper_trade.abc_backtest_controller import ABCBacktestController
from blankly.exchanges.exchange import ABCExchange
from blankly.data.data_reader import PriceReader, EventReader, TickReader


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
                                          positive_ranges[i + 1][0], positive_ranges[i + 1][1])
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
        negative_ranges.append([positive_ranges[i][1], positive_ranges[i + 1][0]])

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


class BackTestController(ABCBacktestController):  # circular import to type model
    def __init__(self, model):
        self.backtesting = False
        self.preferences = None
        self.backtest_settings_path = None

        self.interface = None

        self.initial_time = None
        self.model = model

        self.traded_account_values = []
        self.no_trade_account_values = []

        # Prices sorted by symbol and then records of prices
        self.prices = {}
        # A list of events sorted by time. All events are put into this single list
        self.events = []

        # User added times
        self.__user_added_times = []

        # Open, high, low, close or volume
        self.use_price = None

        # Should we write to the preferences?
        self.queue_backtest_write = False

        # The quote currency to use
        self.quote_currency = None

        # Create a global generator because a second yield function gets really nasty
        # This is used for the colors of the graphs
        self.__color_generator = Category10_10.__iter__()

        # Some initial account value to store globally
        self.initial_account = None

        # Create our own traded assets' dictionary because we customize it a bit
        self.__traded_assets = []

        # Export a time for use in other classes
        self.time = None

        # The smallest amount of time to save
        self.min_resolution = None

        # Set these when prices are added to find the first price and the last price
        self.user_start = None
        self.user_stop = None

        self.show_progress = False
        self.sleep_count = 0

        # Use this global to retain where we are in the prices dictionary by index
        self.price_indexes = {}
        # Use this to keep trace globally of the event index we're using
        self.event_index = 0

        # Custom injected price readers and events readers
        self.__price_readers = []
        self.__event_readers = []
        self.__tick_readers = []

    class PriceIdentifiers(enum.Enum):
        exchange: str = 0
        sandbox: bool = 1
        symbol: str = 2
        epoch_start: int = 3
        epoch_stop: int = 4
        resolution: int = 5

    def parse_events(self):
        """
        Transform to:
        [
            {
                "type": "news event",
                "data": "gotem",
                "time": 2
            }
        ]
        """
        # TODO some code duplication here for the different events
        for reader in self.__event_readers:
            # Get the data as dict of dataframes
            data = reader.data
            for event_type in data:
                self.__check_user_time_bounds(reader.data[event_type]['time'].iloc[0],
                                              reader.data[event_type]['time'].iloc[-1],
                                              60)
                # Get the dataframe in each one
                event_df: pd.DataFrame = data[event_type]
                # Now turn it into a set of records
                records = event_df.to_dict(orient='records')
                # And make sure to add on the event type to each one
                for record_index in range(len(records)):
                    records[record_index]['type'] = event_type

                self.events += records

        for tick_reader in self.__tick_readers:
            data = tick_reader.data
            for symbol in data:
                self.__check_user_time_bounds(tick_reader.data[symbol]['time'].iloc[0],
                                              tick_reader.data[symbol]['time'].iloc[-1],
                                              60)
                symbol_df: pd.DataFrame = data[symbol]

                records = symbol_df.to_dict(orient='records')
                data_formatted_records = []
                for record_index in range(len(records)):
                    data_formatted_records.append({
                        'type': '__blankly__tick',
                        'data': records[record_index],
                        'time': records[record_index]['time']
                    })

                self.events += data_formatted_records

        # Now we just need to sort by time
        self.events = sorted(self.events, key=lambda d: d['time'])

    def sync_prices(self) -> dict:
        """
        Parse the local file cache for the requested data, if it doesn't exist, request it from the exchange

        args:
            items: list of lists organized as ['symbol', 'start_time', 'end_time', 'resolution']

        returns:
            dictionary with keys for each 'symbol'
        """

        # Make sure the cache folder exists and read files
        cache_folder = self.preferences['settings']["cache_location"]

        def sort_prices_by_resolution(price_dict):
            for symbol_ in price_dict:
                for resolution_ in price_dict[symbol_]:
                    price_dict[symbol_][resolution_] = price_dict[symbol_][resolution_].sort_values(by=['time'],
                                                                                                    ignore_index=True)

            return price_dict

        def aggregate_prices_by_resolution(price_dict, symbol_, resolution_, data_) -> dict:
            if symbol_ not in price_dict:
                price_dict[symbol_] = {}
            # Concat after the resolution check here
            if resolution_ not in price_dict[symbol_]:
                price_dict[symbol_][resolution_] = data_
            else:
                price_dict[symbol_][resolution_] = pd.concat([price_dict[symbol_][resolution_],
                                                              data_])
            return price_dict

        def parse_identifiers() -> list:
            try:
                files = os.listdir(cache_folder)
            except FileNotFoundError:
                files = []
                os.mkdir(cache_folder)

            identifiers_ = []
            for file in range(len(files)):
                # example file name: 'coinbase_pro.sandbox.BTC-USD.1622400000.1622510793.60.csv'
                # Remove the .csv from each of the files: BTC-USD.1622400000.1622510793.60
                identifier = files[file][:-4].split(",")
                # Cast to float first before
                try:
                    identifiers_.append({
                        self.PriceIdentifiers.exchange: identifier[0],
                        self.PriceIdentifiers.sandbox: identifier[1] == 'True',
                        self.PriceIdentifiers.symbol: identifier[2],
                        self.PriceIdentifiers.epoch_start: int(float(identifier[3])),
                        self.PriceIdentifiers.epoch_stop: int(float(identifier[4])),
                        self.PriceIdentifiers.resolution: int(float(identifier[5]))
                    })
                except IndexError:
                    # Remove each of the failed cache objects
                    os.remove(os.path.join(cache_folder, files[file]))

            return identifiers_

        def sort_identifiers(identifiers_: list) -> dict:
            """
            Create the hierarchy based on the identifiers
            {
                'coinbase_pro': {
                    True: {
                        'BTC-USD': [60, 3600, 86400]
                    }
                    False: {

                    }
                }
            }
            """
            local_history_blocks_ = {}

            def sort_identifier(identifier_: dict):
                exchange_ = identifier_[self.PriceIdentifiers.exchange]
                sandbox_ = identifier_[self.PriceIdentifiers.sandbox]
                symbol_ = identifier_[self.PriceIdentifiers.symbol]
                resolution_ = identifier_[self.PriceIdentifiers.resolution]

                if exchange_ not in local_history_blocks_:
                    local_history_blocks_[exchange_] = {}

                if sandbox_ not in local_history_blocks_[exchange_]:
                    local_history_blocks_[exchange_][sandbox_] = {}

                if symbol_ not in local_history_blocks_[exchange_][sandbox_]:
                    local_history_blocks_[exchange_][sandbox_][symbol_] = {}

                # Now we're checking the resolution array
                if resolution_ not in local_history_blocks_[exchange_][sandbox_][symbol_]:
                    local_history_blocks_[exchange_][sandbox_][symbol_][resolution_] = []

                # Add these in as a dictionary
                local_history_blocks_[exchange_][sandbox_][symbol_][resolution_].append({
                    self.PriceIdentifiers.epoch_start: identifier_[self.PriceIdentifiers.epoch_start],
                    self.PriceIdentifiers.epoch_stop: identifier_[self.PriceIdentifiers.epoch_stop]
                })

            # This is only the downloaded data
            for identifier in identifiers_:
                sort_identifier(identifier)

            return local_history_blocks_

        identifiers = parse_identifiers()

        local_history_blocks = sort_identifiers(identifiers)

        final_prices: dict = {}
        prices_by_resolution: dict = {}
        for i in range(len(self.__user_added_times)):
            if self.__user_added_times[i] is None:
                continue
            symbol = self.__user_added_times[i][self.PriceIdentifiers.symbol]
            resolution = self.__user_added_times[i][self.PriceIdentifiers.resolution]
            start_time = self.__user_added_times[i][self.PriceIdentifiers.epoch_start]
            end_time = self.__user_added_times[i][self.PriceIdentifiers.epoch_stop] - resolution
            exchange = self.interface.get_exchange_type()
            sandbox = True

            if end_time < start_time:
                raise RuntimeError("Must specify a longer timeframe to run the backtest.")

            downloaded_ranges = []

            # Attempt to find the same symbol/asset possibilities in the backtest blocks
            try:
                # Make sure to copy it because if you don't you delete this for any similar resolution
                # If you don't copy it fails if you use two price events at the same resolution
                available_prices = copy.deepcopy(local_history_blocks[exchange][sandbox][symbol][resolution])
                # Pull the epoch start and epoch stop for this particular symbol / resolution
                for price_set in available_prices:
                    downloaded_ranges.append([
                        price_set[self.PriceIdentifiers.epoch_start],
                        price_set[self.PriceIdentifiers.epoch_stop]
                    ])
            except KeyError:
                pass

            used_ranges, negative_ranges = split([start_time, end_time], downloaded_ranges)

            relevant_data = []
            for j in used_ranges:
                relevant_data.append(pd.read_csv(os.path.join(cache_folder, to_string_key([exchange,
                                                                                           True,
                                                                                           symbol,
                                                                                           j[0],
                                                                                           j[1],
                                                                                           resolution]) + ".csv")))

            if len(relevant_data) > 0:
                final_prices[symbol] = pd.concat(relevant_data)
                for dataset in relevant_data:
                    prices_by_resolution = aggregate_prices_by_resolution(prices_by_resolution, symbol, resolution,
                                                                          dataset)

            # If there is any data left to download do it here
            for j in negative_ranges:
                print("No cached data found for " + symbol + " from: " + str(j[0]) + " to " +
                      str(j[1]) + " at a resolution of " + str(resolution) + " seconds.")
                download = self.interface.get_product_history(symbol,
                                                              j[0],
                                                              j[1],
                                                              resolution)

                # Write the file but this time include very accurately the start and end times
                if self.preferences['settings']['continuous_caching']:
                    if not download.empty:
                        download.to_csv(os.path.join(cache_folder, f'{exchange},'
                                                                   f'{True},'
                                                                   f'{symbol},'
                                                                   f'{int(j[0])},'
                                                                   f'{int(j[1]) + resolution},'  # This adds resolution 
                                                                                                 # back to the exported
                                                                                                 # time series
                                                                   f'{resolution}.csv'),
                                        index=False)

                prices_by_resolution = aggregate_prices_by_resolution(prices_by_resolution, symbol, resolution,
                                                                      download)
                # Write these into the data array
                if symbol not in final_prices:
                    final_prices[symbol] = download
                else:
                    final_prices[symbol] = pd.concat([final_prices[symbol], download])

            # After all the negative ranges are appended, we need to sort & trim
            final_prices[symbol] = final_prices[symbol].sort_values(by=['time'], ignore_index=True)

            # Now make sure to just trim our times to hit the start and end times
            final_prices[symbol] = final_prices[symbol][final_prices[symbol]['time'] >= start_time]
            final_prices[symbol] = final_prices[symbol][
                final_prices[symbol]['time'] <= end_time + resolution]  # Add back

        # Now add any custom prices
        for price_reader in self.__price_readers:
            data = price_reader.data
            for symbol in data:
                symbol_info = price_reader.prices_info[symbol]
                resolution = symbol_info['resolution']
                start_time = symbol_info['start_time']
                stop_time = symbol_info['stop_time']

                # Add each symbol to the final prices without doing any processing
                if symbol in final_prices:
                    final_prices[symbol] = pd.concat([final_prices[symbol], data[symbol]])
                else:
                    final_prices[symbol] = data[symbol]

                prices_by_resolution = aggregate_prices_by_resolution(prices_by_resolution, symbol, resolution,
                                                                      data[symbol])

                self.__check_user_time_bounds(start_time,
                                              stop_time,
                                              resolution)

        # Send the prices by resolution to the interface
        self.interface.receive_price_cache(sort_prices_by_resolution(prices_by_resolution))

        # Finally, convert back into records
        for symbol in final_prices:
            final_prices[symbol] = final_prices[symbol].to_records()

        return final_prices

    def add_prices(self,
                   symbol: str,
                   resolution: [str, int, float],
                   to: str = None,
                   start_date: typing.Union[str, float, int] = None,
                   stop_date: typing.Union[str, float, int] = None):
        """
        This is the user facing function for adding prices to the engine
        """
        start = None
        end = None

        resolution = int(time_interval_to_seconds(resolution))

        # Even if they specified start/end unevenly it will be overwritten with any to argument
        if to is not None:
            start = time.time() - time_interval_to_seconds(to)
            end = time.time()

        if start_date is not None:
            if isinstance(stop_date, (int, float)):
                start = start_date
            else:
                start_date = pd.to_datetime(start_date)
                epoch = dt.utcfromtimestamp(0)
                start = (start_date - epoch).total_seconds()

        if stop_date is not None:
            if isinstance(stop_date, (int, float)):
                end = stop_date
            else:
                end_date = pd.to_datetime(stop_date)
                epoch = dt.utcfromtimestamp(0)
                end = (end_date - epoch).total_seconds()

        # If start/ends are specified unevenly
        if (start_date is None and stop_date is not None) or (start_date is not None and stop_date is None):
            raise ValueError("Both start and end dates must be set or use the 'to' argument.")

        self.__add_prices(symbol, start, end, resolution)

    def add_custom_prices(self, price_reader: PriceReader):
        self.__price_readers.append(price_reader)

    def add_custom_events(self, event_reader: EventReader):
        self.__event_readers.append(event_reader)

    def add_tick_events(self, tick_reader: TickReader):
        self.__tick_readers.append(tick_reader)

    def __add_prices(self, symbol, start_time, end_time, resolution, save=False):
        # If it's not loaded then write it to the file
        # Add it as a new price
        self.__user_added_times.append({
            self.PriceIdentifiers.sandbox: True,
            self.PriceIdentifiers.symbol: symbol,
            self.PriceIdentifiers.resolution: resolution,
            self.PriceIdentifiers.epoch_start: start_time,
            self.PriceIdentifiers.epoch_stop: end_time
        })
        if save:
            self.queue_backtest_write = True

        self.__check_user_time_bounds(start_time, end_time, resolution)

    def __check_user_time_bounds(self, start_time, end_time, resolution):
        # This makes sure that we keep track of our bounds which is just generally kind of useful
        # Any time a new price event is added we check this
        if self.user_start is None:
            self.user_start = start_time
        else:
            if start_time < self.user_start:
                self.user_start = start_time

        if self.user_stop is None:
            self.user_stop = end_time
        else:
            if end_time > self.user_stop:
                self.user_stop = end_time

        # Now keep track of the smallest price event added
        if self.min_resolution is None:
            self.min_resolution = resolution
        else:
            if resolution < self.min_resolution:
                self.min_resolution = resolution

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

    def __write_initial_price_values(self, account_dictionary):
        """
        Write in a new price dictionary for the paper trade exchange.
        """
        self.interface.override_local_account(account_dictionary)

    def format_account_data(self, interface: PaperTradeInterface, local_time) -> \
            typing.Tuple[typing.Dict[
                             typing.Union[
                                 str, typing.Any],
                             typing.Union[
                                 int, typing.Any]],
                         typing.Dict[
                             typing.Union[str,
                                          typing.Any],
                             typing.Union[
                                 int, typing.Any]]]:

        # This is done so that only traded assets are evaluated.
        true_available = {}
        true_account = {}
        for i in interface.traded_assets:
            # Grab the account status
            true_account[i] = interface.get_account(i)

        # Create an account total value
        value_total = 0

        no_trade_available = {}
        # No trade account total
        no_trade_value = 0

        # Save this up front so that it can be removed from the price calculation (it's always a value of 1 anyway)
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
            if interface.get_exchange_type() != 'alpaca':
                currency_pair += '-'
                currency_pair += self.quote_currency

            # Get price at time
            try:
                price = interface.get_price(currency_pair)
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

        no_trade_value += self.initial_account[self.quote_currency][
                              'available'] + self.initial_account[self.quote_currency]['hold']

        true_available['Account Value (' + self.quote_currency + ')'] = value_total

        no_trade_available['Account Value (No Trades)'] = no_trade_value

        return true_available, no_trade_available

    def __account_was_used(self, column) -> bool:
        show_zero_delta = self.preferences['settings']['show_tickers_with_zero_delta']

        # Just check if it's in the traded assets or if the zero delta is enabled
        is_used = column in self.interface.traded_assets or 'Account Value (' + self.quote_currency + ')' == column

        # Return true if they are not the same or the setting is set to true
        output = is_used or show_zero_delta
        return output

    def __next_color(self):
        # This should be a generator, but it doesn't work without doing a foreach loop
        try:
            return next(self.__color_generator)
        except StopIteration:
            self.__color_generator = Category10_10.__iter__()
            return next(self.__color_generator)

    def advance_time_and_price_index(self):
        def handle_blankly_tick(type_: str, data):
            if type_ == 'tick':
                self.model.websocket_update(data)

        def run_events():
            # Ensure that we don't index error here
            events_length = len(self.events)
            # Make sure we don't crash at first
            if self.event_index >= events_length:
                return

            # Store the time because we need accurate time for the async stuff
            time_backup = self.time
            while self.events[self.event_index]['time'] < time_backup:
                # Set time to something different here
                event = self.events[self.event_index]
                self.time = event['time']
                if event['type'][0:11] != '__blankly__':
                    self.model.event(event['type'], event['data'])
                else:
                    handle_blankly_tick(event['type'][11:], event['data'])
                # Fired some event, go to the next one
                self.event_index += 1

                # Just check after doing that if we went outside the index
                if self.event_index >= events_length:
                    return

            self.time = time_backup

        # Now update the time to match
        self.interface.receive_time(self.time)

        for symbol in self.prices:
            # Make sure that each price column is at least at the current time

            # This just incrementing the price indexes until it's less than time and ensuring that
            #  it's less than the length of the price
            price_length = len(self.prices[symbol]) - 2
            while self.prices[symbol][self.price_indexes[symbol]]['time'] < self.time:
                if price_length >= self.price_indexes[symbol]:
                    self.price_indexes[symbol] += 1
                else:
                    self.model.has_data = False
                    break

            # Write this new price into the interface
            self.interface.receive_price(symbol, new_price=self.prices[symbol][
                self.price_indexes[symbol]][self.use_price])

        # Check has_data here also
        if self.time > self.user_stop:
            self.model.has_data = False

        run_events()

    def sleep(self, seconds: [int, float]):
        # Always evaluate limits
        self.interface.evaluate_limits()
        self.sleep_count += 1

        if self.show_progress:
            if self.sleep_count % 300 == 0:
                # Update the progress occasionally
                update_progress((self.time - self.user_start) / (self.user_stop - self.user_start))

        # Advance the time
        self.time += seconds
        # Refresh all the prices and times
        self.advance_time_and_price_index()

    def value_account(self) -> None:
        """
        Store the valuation for the account

        This is accessible by the user
        """
        # Don't do anything when live
        if not self.backtesting:
            return

        available_dict, no_trade_dict = self.format_account_data(self.interface, self.time)

        self.traded_account_values.append(available_dict)
        self.no_trade_account_values.append(no_trade_dict)

    # TODO this class should be constructed with a BacktestConfiguration object
    def run(self,
            args,
            exchange: ABCExchange,
            initial_account_values,
            backtest_settings_path: str = None,
            **kwargs) -> BacktestResult:
        """
        Setup
        """
        self.backtesting = True
        self.preferences = load_backtest_preferences(backtest_settings_path)
        # Write any dynamic arguments back into the backtest preferences
        for setting in kwargs:
            self.preferences['settings'][setting] = kwargs[setting]

        self.backtest_settings_path = backtest_settings_path
        self.show_progress = self.preferences['settings']['show_progress_during_backtest']

        if not exchange.get_type() == "paper_trade":
            raise ValueError("Backtest controller was not constructed with a paper trade exchange object.")
        # Define the interface on run
        self.interface: PaperTradeInterface = exchange.get_interface()
        # This is where we begin logging the backtest time
        start_clock = time.time()

        # Figure out our traded assets here
        self.prices = self.sync_prices()
        # Now ensure all events are processed
        self.parse_events()
        for i in self.prices:
            base = get_base_asset(i)
            quote = get_quote_asset(i)
            if base not in self.interface.traded_assets:
                self.interface.traded_assets.append(base)
            if quote not in self.interface.traded_assets:
                self.interface.traded_assets.append(quote)

        # Write them in
        if initial_account_values is not None:
            self.__write_initial_price_values(initial_account_values)

        # Write our queued edits to the file
        if self.queue_backtest_write:
            write_backtest_preferences(self.preferences, self.backtest_settings_path)

        # TODO the preferences should really be reloaded here so that micro changes such as the quote currency reset
        #  don't need to happen for every single key type
        self.quote_currency = self.preferences['settings']['quote_account_value_in']

        # Get the symbol used for the benchmark
        benchmark_symbol = self.preferences["settings"]["benchmark_symbol"]

        if benchmark_symbol is not None:
            # Check locally for the data and add to price_cache if we do not have it
            self.add_prices(benchmark_symbol, start_date=self.user_start, stop_date=self.user_stop,
                            resolution=self.min_resolution)

        use_price = self.preferences['settings']['use_price']
        self.use_price = use_price

        for frame_symbol, price_list in self.prices.items():
            # This is a list of dictionaries
            frame = price_list  # type: list

            # Be sure to push these initial prices to the strategy
            try:
                self.interface.receive_price(frame_symbol, frame[0][use_price])
            except IndexError:
                def check_if_any_column_has_prices(price_dict: dict) -> bool:
                    """
                    In dictionary of symbols, check if at least one key has data
                    """
                    for j in price_dict:
                        # This handles the weird types
                        if len(price_dict[j]) == 0:
                            return False
                        if not price_dict[j].empty:
                            return True
                    return False

                if not check_if_any_column_has_prices(self.prices):
                    raise IndexError('No cached or downloaded data available. Try adding arguments such as to="1y" '
                                     'in the backtest command. If there should be data downloaded, try deleting your'
                                     ' ./price_caches folder.')
                else:
                    raise IndexError(f"Data for symbol {frame_symbol} is empty. Are you using a symbol that "
                                     f"is incompatible "
                                     f"with this exchange?")

            # Be sure to send in the initial time
            first_time = price_list['time'][0]
            self.interface.receive_time(first_time)
            self.price_indexes[frame_symbol] = 0

            # Find the first time in the list
            self.initial_time = copy.copy(self.user_start)

        if self.prices == {} and self.events == []:
            raise ValueError("No data given. "
                             "Try setting an argument such as to='1y' in the .backtest() command.\n"
                             "Example: strategy.backtest(to='1y')")

        """
        Begin backtesting
        """
        # Create this initial so that we can compare how our strategy performs
        self.initial_account = self.interface.get_account()

        # Initialize this before the callbacks, so it works in the initialization functions
        self.time = copy.copy(self.user_start)

        # Turn on backtesting immediately after setting the time
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
        column_keys.append('time')

        cycle_status = pd.DataFrame(columns=column_keys)

        no_trade_cycle_status = pd.DataFrame(columns=column_keys)

        # Add an initial account row here
        if self.preferences['settings']['save_initial_account_value']:
            available_dict, no_trade_dict = self.format_account_data(self.interface, self.user_start)
            self.traded_account_values.append(available_dict)
            self.no_trade_account_values.append(no_trade_dict)

        print("\nBacktesting...")

        # Start the model here
        try:
            self.model.main(args)
            if self.show_progress:
                # If it finishes give it 100%
                update_progress(1)
        except Exception:
            traceback.print_exc()

        # Reset time to indicate we are no longer in a backtest
        self.time = None

        # Push the accounts to the dataframe
        cycle_status = pd.concat([cycle_status, pd.DataFrame(self.traded_account_values)],
                                 ignore_index=True).sort_values(by=['time'])

        if len(cycle_status) == 0:
            raise RuntimeError("Empty result - no valid backtesting events occurred. Was there an error?.")

        no_trade_cycle_status = pd.concat([no_trade_cycle_status, pd.DataFrame(self.no_trade_account_values)],
                                          ignore_index=True).sort_values(by=['time'])

        def is_number(s):
            try:
                float(s)
                # Love how bools cast to a number
                return not isinstance(s, bool)
            except ValueError:
                return False

        history_and_returns: dict = {
            'history': cycle_status
        }
        metrics_indicators = {}
        user_callbacks = {}

        result_object = BacktestResult(history_and_returns, {
            'created': self.interface.paper_trade_orders,
            'limits_executed': self.interface.executed_orders,
            'limits_canceled': self.interface.canceled_orders,
            'executed_market_orders': self.interface.market_order_execution_details
        }, self.prices, self.initial_time, self.interface.time(), self.quote_currency, [])

        # If they set resampling we use resampling for everything
        resample_setting = self.preferences['settings']['resample_account_value_for_metrics']
        if isinstance(resample_setting, str) or is_number(resample_setting):
            resample_to = resample_setting
        else:
            info_print('Resampling value not set, defaulting to 1 day.')
            resample_to = '1d'

        interval_value = time_interval_to_seconds(resample_to)

        # This is where we run the actual resample
        resampled_account_data_frame = result_object.resample_account('Account Value (' + self.quote_currency + ')',
                                                                      interval_value)

        history_and_returns['resampled_account_value'] = resampled_account_data_frame

        returns = resampled_account_data_frame.copy(deep=True)

        # Default diff parameters should do it
        returns['value'] = returns['value'].pct_change()

        # Now write it to our dictionary
        history_and_returns['returns'] = returns

        # -----=====*****=====-----
        metrics_indicators['Compound Annual Growth Rate (%)'] = metrics.cagr(history_and_returns)
        try:
            metrics_indicators['Cumulative Returns (%)'] = metrics.cum_returns(history_and_returns)
        except ZeroDivisionError as e_:
            metrics_indicators['Cumulative Returns (%)'] = f'failed: {e_}'

        def attempt(math_callable: typing.Callable, dict_of_dataframes: dict, kwargs: dict = None):
            try:
                if kwargs is None:
                    kwargs = {}
                result = math_callable(dict_of_dataframes, **kwargs)
                if result == np.NAN:
                    result = None
                return result
            except (ZeroDivisionError, Exception) as e__:
                return f'failed: {e__}'

        risk_free_return_rate = self.preferences['settings']["risk_free_return_rate"]
        metrics_indicators['Max Drawdown (%)'] = attempt(metrics.max_drawdown, history_and_returns)
        metrics_indicators['Variance (%)'] = attempt(metrics.variance, history_and_returns,
                                                     {'trading_period': interval_value})
        metrics_indicators['Sortino Ratio'] = attempt(metrics.sortino, history_and_returns,
                                                      {'risk_free_rate': risk_free_return_rate,
                                                       'trading_period': interval_value})
        metrics_indicators['Sharpe Ratio'] = attempt(metrics.sharpe, history_and_returns,
                                                     {'risk_free_rate': risk_free_return_rate,
                                                      'trading_period': interval_value})
        metrics_indicators['Calmar Ratio'] = attempt(metrics.calmar, history_and_returns,
                                                     {'trading_period': interval_value})
        metrics_indicators['Volatility'] = attempt(metrics.volatility, history_and_returns,
                                                   {'trading_period': interval_value})
        metrics_indicators['Value-at-Risk'] = attempt(metrics.var, history_and_returns)
        metrics_indicators['Conditional Value-at-Risk'] = attempt(metrics.cvar, history_and_returns)

        # Add risk-free-return rate to dictionary
        metrics_indicators['Risk Free Return Rate'] = risk_free_return_rate
        # metrics_indicators['beta'] = attempt(metrics.beta, dataframes)
        # Add the interval value to dictionary
        metrics_indicators['Resampled Time'] = interval_value
        # -----=====*****=====-----

        # If a benchmark was requested, add it to the pd_prices frame
        if benchmark_symbol is not None:
            # Resample the benchmark results
            resampled_benchmark_value = result_object.resample_account(benchmark_symbol,
                                                                       interval_value,
                                                                       use_asset_history=True,
                                                                       use_price=use_price)

            # Push data into the dictionary for use by the metrics
            history_and_returns['benchmark_value'] = resampled_benchmark_value
            history_and_returns['benchmark_returns'] = resampled_benchmark_value.copy(deep=True)
            history_and_returns['benchmark_returns']['value'] = history_and_returns['benchmark_returns'][
                'value'].pct_change()

            # Calculate beta
            metrics_indicators['Beta'] = attempt(metrics.beta, history_and_returns,
                                                 {"trading_period": interval_value})

        # Remove NaN values here
        history_and_returns['resampled_account_value'] = history_and_returns['resampled_account_value']. \
            where(history_and_returns['resampled_account_value'].notnull(), None)

        # Remove NaN values on this one too
        history_and_returns['returns'] = history_and_returns['returns'].where(history_and_returns['returns'].notnull(),
                                                                              None)
        # Lastly remove Nan values in the metrics
        for i in metrics_indicators:
            if not isinstance(metrics_indicators[i], str) and np.isnan(metrics_indicators[i]):
                metrics_indicators[i] = None

        # Assign all these new values back to the result object
        result_object.history_and_returns = history_and_returns
        result_object.metrics = metrics_indicators
        result_object.user_callbacks = user_callbacks
        result_object.exchange = self.interface.get_exchange_type()

        figures = []
        # This modifies the platform result in place
        platform_result = format_platform_result(result_object)
        if self.preferences['settings']['GUI_output']:
            def internal_backtest_viewer():
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

                # Define a helper function to avoid repeating code
                def add_trace(self_, figure_, time__, data_, label):
                    source = ColumnDataSource(data=dict(
                        time=time__,
                        value=data_.values.tolist()
                    ))
                    figure_.step('time', 'value',
                                 source=source,
                                 line_width=2,
                                 color=self_.__next_color(),
                                 legend_label=label,
                                 mode="after")

                global_x_range = None

                time_ = [dt.fromtimestamp(ts) for ts in cycle_status['time']]

                for column in cycle_status:
                    if column != 'time' and self.__account_was_used(column):
                        p = figure(plot_width=900, plot_height=200, x_axis_type='datetime')
                        add_trace(self, p, time_, cycle_status[column], column)

                        # Add the no-trade line to the backtest
                        if column == 'Account Value (' + self.quote_currency + ')':
                            add_trace(self, p, time_, no_trade_cycle_status['Account Value (No Trades)'],
                                      'Account Value (No Trades)')

                            # Add the benchmark, if requested
                            if benchmark_symbol is not None:
                                # This normalizes the benchmark value
                                initial_account_value = cycle_status['Account Value (' +
                                                                     self.quote_currency + ')'].iloc[0]
                                benchmark_series = pd.Series(self.prices[benchmark_symbol][use_price])
                                initial_benchmark_value = benchmark_series.iloc[0]

                                # This multiplier brings the initial asset price to the initial account value
                                # initial_account_value = initial_benchmark_value * x
                                multiplier = initial_account_value / initial_benchmark_value

                                normalized_compare_series = benchmark_series.multiply(multiplier)
                                normalized_compare_time_series = self.prices[benchmark_symbol]['time']

                                # We need to also cast the time series that is needed to compare
                                # because it's only been done for the cycle status time
                                normalized_compare_time_series = [dt.fromtimestamp(ts) for ts in
                                                                  normalized_compare_time_series]
                                add_trace(self, p, normalized_compare_time_series,
                                          normalized_compare_series,
                                          f'Normalized Benchmark ({benchmark_symbol})')

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
                info_print(f'Make an account to take advantage of the platform backtest viewer: '
                           f'https://app.blankly.finance/RETIe0J8EPSQz7wizoJX0OAFb8y1/EZkgTZMLJVaZK6kNy0mv/'
                           f'2b2ff92c-ee41-42b3-9afb-387de9e4f894/backtest')

            # This is where we end the backtesting time
            stop_clock = time.time()

            try:
                json_file = json.loads(open('./blankly.json').read())
                api_key = json_file['api_key']
                api_pass = json_file['api_pass']
                # Need this to generate the URL
                # Need this to know where to post to
                model_id = json_file['model_id']

                requests.post(f'https://events.blankly.finance/v1/backtest/result', json=platform_result, headers={
                    'api_key': api_key,
                    'api_pass': api_pass,
                    'model_id': model_id
                })

                requests.post(f'https://events.blankly.finance/v1/backtest/status', json={
                    'successful': True,
                    'status_summary': 'Completed',
                    'status_details': '',
                    'time_elapsed': stop_clock-start_clock,
                    'backtest_id': platform_result['backtest_id']
                }, headers={
                    'api_key': api_key,
                    'api_pass': api_pass,
                    'model_id': model_id
                })

                import webbrowser

                link = f'https://app.blankly.finance/{api_key}/{model_id}/{platform_result["backtest_id"]}' \
                       f'/backtest'
                webbrowser.open(
                    link
                )
                info_print(f'View your backtest here: {link}')
            except (FileNotFoundError, KeyError):
                internal_backtest_viewer()

        # Finally, write the figures in
        result_object.figures = figures

        self.interface.set_backtesting(False)
        self.backtesting = False

        # Export to the platform here
        blankly.reporter.export_backtest_result(platform_result)

        return result_object
