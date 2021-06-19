"""
    Abstraction for creating event driven user strategies
    Copyright (C) 2021  Emerson Dove, Brandon Fan

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
import warnings

from Blankly.strategy.strategy_state import StrategyState
from Blankly.utils.utils import AttributeDict
import typing
import time

import pandas as pd
import datetime
import Blankly
from Blankly.exchanges.Paper_Trade.backtest_controller import BackTestController
from uuid import uuid4
from Blankly.exchanges.exchange import Exchange
from Blankly.utils.time_builder import time_interval_to_seconds


class Strategy:
    def __init__(self, exchange: Exchange, currency_pair='BTC-USD'):
        self.__exchange = exchange
        self.Ticker_Manager = Blankly.TickerManager(self.__exchange.get_type(), currency_pair)
        self.Orderbook_Manager = Blankly.OrderbookManager(self.__exchange.get_type(), currency_pair)

        self.__scheduling_pair = []  # Object to hold a currency and the resolution its pulled at: ["BTC-USD", 60]
        self.Interface = exchange.get_interface()

        # Create a cache for the current interface, and a wrapped paper trade object for user backtesting
        self.__interface_cache = self.Interface
        self.__paper_trade_exchange = Blankly.PaperTrade(self.__exchange)
        self.__schedulers = []
        self.__variables = {}

    def add_price_event(self, callback: typing.Callable, currency_pair: str, resolution: str):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            currency_pair: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
        """
        resolution = time_interval_to_seconds(resolution)
        
        self.__scheduling_pair.append([currency_pair, resolution])
        callback_id = str(uuid4())
        self.__variables[callback_id] = AttributeDict({})
        if resolution < 10:
            # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
            self.Ticker_Manager.create_ticker(self.__idle_event, currency_id=currency_pair)
            self.__schedulers.append(
                Blankly.Scheduler(self.__price_event_websocket, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  resolution=resolution,
                                  variables=self.__variables[callback_id],
                                  currency_pair=currency_pair)
            )
        else:
            # Use the API
            self.__schedulers.append(
                Blankly.Scheduler(self.__price_event_rest, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  resolution=resolution,
                                  variables=self.__variables[callback_id],
                                  currency_pair=currency_pair)
            )

    def __idle_event(self):
        """
        Function to skip & ignore callbacks
        """
        pass
        
    def __price_event_rest(self, **kwargs):
        callback = kwargs['callback']
        currency_pair = kwargs['currency_pair']
        resolution = kwargs['resolution']
        variables = kwargs['variables']
        price = self.Interface.get_price(currency_pair)

        state = StrategyState(self, self.Interface, variables, resolution)
        return callback(price, currency_pair, state)

    def __price_event_websocket(self, **kwargs):
        callback = kwargs['callback']
        currency_pair = kwargs['currency_pair']
        resolution = kwargs['resolution']
        variables = kwargs['variables']

        price = self.Ticker_Manager.get_most_recent_tick(override_currency=currency_pair)
        state = StrategyState(self, self.Interface, variables, resolution)
        return callback(price, currency_pair, state)

    def add_orderbook_event(self, callback: typing.Callable, currency_pair: str):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            currency_pair: Currency pair to create the orderbook for
        """
        # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
        self.Orderbook_Manager.create_orderbook(callback, currency_id=currency_pair)

    def start(self):
        for i in self.__schedulers:
            i.start()
    
    def backtest(self, 
                 initial_values: dict = None,
                 to: str = None,
                 start_date: str = None,
                 end_date: str = None,
                 save: bool = False,
                 settings_path: str = None,
                 callbacks: list = None,
                 **kwargs
                 ):
        """
        Turn this strategy into a backtest.

        Args:
            ** We expect either an initial_value (in USD) or a dictionary of initial values, we also expect
            either `to` to be set or `start_date` and `end_date` **

            initial_values (dict): Dictionary of initial value sizes (i.e { 'BTC': 3, 'USD': 5650}).
                Using this will override the values that are currently on your exchange.
            to (str): Declare an amount of time before now to backtest from: ex: '5y' or '10h'
            start_date (str): Override argument "to" by specifying a start date such as "03/06/2018"
            end_date (str): End the backtest at a date such as "03/06/2018"
            save (bool): Save the price data references to the data required for the backtest as well as
                overriden settings.
            settings_path (str): Path to the backtest.json file.
            callbacks (list of callables): Custom functions that will be run at the end of the backtest

            Keyword Arguments:
                **Use these to override parameters in the backtest.json file**

                use_price: str = 'close',
                    Set which price column to use.

                smooth_prices: bool = False,
                    Create linear connections between downloaded prices

                GUI_output: bool = True,
                    Enable/disable GUI webpage display after backtest

                show_tickers_with_zero_delta: bool = False,
                    Exclude tickers that have no change to account value in the GUI

                save_initial_account_value: bool = True,
                    Put an extra frame which contains the initial account values before any trade

                show_progress_during_backtest: bool = True,
                    Show a progress bar as the backtest runs

                cache_location: str = './price_caches'
                    Set a location for the price cache csv's to be written to
        """

        start = None
        end = None

        if to is not None:
            start = time.time() - time_interval_to_seconds(to)
            end = time.time()

        if start_date is not None:
            start_date = pd.to_datetime(start_date)
            epoch = datetime.datetime.utcfromtimestamp(0)
            start = (start_date - epoch).total_seconds()

        if end_date is not None:
            end_date = pd.to_datetime(end_date)
            epoch = datetime.datetime.utcfromtimestamp(0)
            end = (end_date - epoch).total_seconds()

        self.Interface = self.__paper_trade_exchange.get_interface()
        backtesting_controller = BackTestController(self.__paper_trade_exchange,
                                                    backtest_settings_path=settings_path,
                                                    callbacks=callbacks
                                                    )

        # Write any kwargs as settings to the settings - save if enabled.
        for k, v in kwargs.items():
            backtesting_controller.write_setting(k, v, save)

        if initial_values is not None:
            backtesting_controller.write_initial_price_values(initial_values)

        # Write each scheduling pair as a price event - save if enabled.
        if start is not None and end is not None:
            for i in self.__scheduling_pair:
                backtesting_controller.add_prices(i[0], start, end, i[1], save=save)
        else:
            warnings.warn("User-specified start and end time not given. Defaulting to using only cached data.")

        # Append each of the events the class defines into the backtest
        for i in self.__schedulers:
            kwargs = i.get_kwargs()
            backtesting_controller.append_backtest_price_event(callback=kwargs['callback'],
                                                               asset_id=kwargs['currency_pair'],
                                                               time_interval=i.get_interval()
                                                               )

        # Run the backtest & return results
        results = backtesting_controller.run()

        # Clean up
        self.Interface = self.__interface_cache
        return results
