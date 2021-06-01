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

from Blankly.exchanges.Paper_Trade.Paper_Trade import PaperTrade
from Blankly.utils.time_builder import time_interval_to_seconds
from Blankly.utils.utils import load_backtest_preferences
import typing
import pandas as pd
import traceback
from bokeh.plotting import figure, show
from bokeh.palettes import Category10_10
import os


class BackTestController:
    def __init__(self, paper_trade_exchange: PaperTrade):
        self.preferences = load_backtest_preferences()
        self.interface = paper_trade_exchange.get_interface()

        self.backtest_price_events = []

    def download_prices(self):
        cache_folder = self.preferences['price_data']["cache_location"]
        # Make sure the cache folder exists and read files
        try:
            files = os.listdir(cache_folder)
        except FileNotFoundError:
            files = []
            os.mkdir(cache_folder)

        split_files = []
        for i in range(len(files)):
            # example file name: 'BTC-USD.1622400000.1622510793.60.csv'
            # Remove the .csv from each of the files: BTC-USD.1622400000.1622510793.60
            split_files.append(files[i].split(".")[1:])

        assets = self.preferences['price_data']['assets']  # type: dict
        price_data = {}
        for k, v in assets.items():
            price_data[k] = self.interface.get_product_history(k, v[0], v[1], v[2])


    def __init__(self, paper_trade_interface: PaperTradeInterface, prices: dict, price_events=None):
        if price_events is None:
            price_events = []  # [[price_event, asset_id, time_interval_to_seconds(interval)]]
        self.price_events = price_events
        self.paper_trade_interface = paper_trade_interface
        self.current_time = 0
        self.prices = []
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

    def append_backtest_price_event(self, callback: typing.Callable, asset_id, time_interval):
        if isinstance(time_interval, str):
            time_interval = time_interval_to_seconds(time_interval)
        self.backtest_price_events.append([callback, asset_id, time_interval])

    def backtest(self):
        # Create arrays of price events along with their interval

        # Create a new controller
        if self.price_data == {} or self.backtest_price_events == []:
            raise ValueError("Either no price data or backtest events given. "
                             "Use .append_backtest_price_data or "
                             "append_backtest_price_event to create the backtest model.")
        else:
            controller = BackTestController(self.get_interface(), self.price_data, self.backtest_price_events)

        # Run the controller
        return controller.run()

    def run(self):
        self.paper_trade_interface.set_backtesting(True)
        account = self.paper_trade_interface.get_account()
        column_keys = ['time']
        for i in account:
            column_keys.append(i['currency'])
        cycle_status = pd.DataFrame(columns=column_keys)

        # Append dictionaries to this to make the pandas dataframe
        price_data = []

        try:
            for price_array in self.prices:
                self.paper_trade_interface.receive_price(price_array[1], price_array[2])
                self.current_time = price_array[0]
                self.paper_trade_interface.receive_time(self.current_time)

                for function_dict in self.price_events:
                    while function_dict['next_run'] <= self.current_time:
                        local_time = function_dict['next_run']
                        # This is the actual callback to the user space
                        function_dict['function'](self.paper_trade_interface.get_price(function_dict['asset_id']),
                                                  function_dict['asset_id'])

                        # Delay the next run until after the interval
                        function_dict['next_run'] += function_dict['interval']

                        available_dict = {}
                        # Grab the account status
                        account_status = self.paper_trade_interface.get_account()
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

        self.paper_trade_interface.set_backtesting(False)
        return cycle_status
