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


from Blankly.exchanges.Paper_Trade.Paper_Trade import PaperTrade
from Blankly.exchanges.Paper_Trade.Paper_Trade_Interface import PaperTradeInterface

from Blankly.utils.time_builder import time_interval_to_seconds
from Blankly.utils.utils import load_backtest_preferences
import typing
import pandas as pd
import traceback
from bokeh.plotting import figure, show
from bokeh.palettes import Category10_10
import os


def to_string_key(separated_list):
    output = ""
    for i in range(len(separated_list) - 1):
        output += separated_list[i]
        output += "."
    output += separated_list[-1:][0]
    return output


class BackTestController:
    def __init__(self, paper_trade_exchange: PaperTrade):
        self.preferences = load_backtest_preferences()
        self.interface = paper_trade_exchange.get_interface()  # type: PaperTradeInterface

        self.price_events = []

        self.current_time = None
        self.initial_time = None

        self.prices = []  # [epoch, "BTC-USD", price]

    def sync_prices(self) -> dict:
        cache_folder = self.preferences['price_data']["cache_location"]
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
            available_files.append(files[i].split(".")[1:])

        price_dictionary = {}

        assets = self.preferences['price_data']['assets']  # type: dict
        for k, v in assets.items():
            identifier = [k, v[0], v[1], v[2]]
            string_identifier = to_string_key(identifier)
            if identifier in available_files:
                # Read the csv here
                price_dictionary[tuple(identifier)] = pd.read_csv(os.path.join(cache_folder,
                                                                               string_identifier + ".csv")
                                                                  )
            else:
                print("No exact cache exists for " + str(identifier[0]) + " from " + str(identifier[1]) + " to " +
                      str(identifier[2]) + " at " + str(identifier[3]) + "s resolution. Downloading...")
                download = self.interface.get_product_history(identifier[0],
                                                              identifier[1],
                                                              identifier[2],
                                                              identifier[3])
                price_dictionary[tuple(identifier)] = download
                download.to_csv(os.path.join(cache_folder, string_identifier + ".csv"), index=False)

        # Merge all the same asset ids into the same dictionary spots
        unique_assets = {}
        for k, v in price_dictionary:
            if k[0] in unique_assets:
                unique_assets[k[0]] = pd.concat([unique_assets[k[0]], v], ignore_index=True)
            else:
                unique_assets[k[0]] = v

        return unique_assets

    def backtest(self):
        prices = self.sync_prices()

        # Organize each price into this structure: [epoch, "BTC-USD", price]
        for k, v in prices.items():
            frame = v  # type: pd.DataFrame
            for index, row in frame.iterrows():
                # TODO this currently only works with open & iterrows() is allegedly pretty slow
                self.prices.append([row.time, k, row.open])

        self.prices = sorted(self.prices, key=lambda x: x[0])

        self.current_time = self.prices[0][0]
        self.initial_time = self.current_time

        # Add a section to the price events which controls the next time they run & change to array of dicts
        for i in range(len(self.price_events)):
            self.price_events[i] = {
                'function': self.price_events[i][0],
                'asset_id': self.price_events[i][1],
                'interval': self.price_events[i][2],
                'next_run': self.initial_time
            }

        if prices == {} or self.price_events == []:
            raise ValueError("Either no price data or backtest events given. "
                             "Use .append_backtest_price_data or "
                             "append_backtest_price_event to create the backtest model.")

        self.run()

    def append_backtest_price_event(self, callback: typing.Callable, asset_id, time_interval):
        if isinstance(time_interval, str):
            time_interval = time_interval_to_seconds(time_interval)
        self.price_events.append([callback, asset_id, time_interval])

    def run(self):
        self.interface.set_backtesting(True)
        account = self.interface.get_account()
        column_keys = ['time']
        for i in account:
            column_keys.append(i['currency'])
        cycle_status = pd.DataFrame(columns=column_keys)

        # Append dictionaries to this to make the pandas dataframe
        price_data = []

        try:
            for price_array in self.prices:
                self.interface.receive_price(price_array[1], price_array[2])
                self.current_time = price_array[0]
                self.interface.receive_time(self.current_time)

                for function_dict in self.price_events:
                    while function_dict['next_run'] <= self.current_time:
                        local_time = function_dict['next_run']
                        # This is the actual callback to the user space
                        function_dict['function'](self.interface.get_price(function_dict['asset_id']),
                                                  function_dict['asset_id'])

                        # Delay the next run until after the interval
                        function_dict['next_run'] += function_dict['interval']

                        available_dict = {}
                        # Grab the account status
                        account_status = self.interface.get_account()
                        for i in account_status:
                            available_dict[i['currency']] = i['available']
                        # Make sure to add the time key in
                        available_dict['time'] = local_time - self.initial_time
                        price_data.append(available_dict)
        except Exception:
            traceback.print_exc()

        # Push the accounts to the dataframe
        cycle_status = cycle_status.append(price_data, ignore_index=True)

        p = figure(plot_width=800, plot_height=900)
        color = Category10_10.__iter__()
        for column in cycle_status:
            if column != 'time':
                p.step(cycle_status['time'].tolist(), cycle_status[column].tolist(),
                       line_width=2,
                       color=next(color),
                       legend_label=column,
                       mode="before"
                       )

        # Format graph
        p.legend.location = "top_left"
        p.legend.title = "Backtest results"
        p.legend.title_text_font_style = "bold"
        p.legend.title_text_font_size = "20px"
        show(p)

        self.interface.set_backtesting(False)
        return cycle_status
