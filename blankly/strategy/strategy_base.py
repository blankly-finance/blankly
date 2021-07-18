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


import datetime
import time
import typing
import warnings

import pandas as pd

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.paper_trade.backtest_controller import BackTestController
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.strategy.strategy_state import StrategyState
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import AttributeDict


class Strategy:
    def __init__(self, exchange: Exchange, currency_pair='BTC-USD'):
        self.__exchange = exchange
        self.Ticker_Manager = blankly.TickerManager(self.__exchange.get_type(), currency_pair)
        self.Orderbook_Manager = blankly.OrderbookManager(self.__exchange.get_type(), currency_pair)

        self.__scheduling_pair = []  # Object to hold a currency and the resolution its pulled at: ["BTC-USD", 60]
        self.Interface = exchange.get_interface()

        # Create a cache for the current interface, and a wrapped paper trade object for user backtesting
        self.__interface_cache = self.Interface
        self.__paper_trade_exchange = blankly.PaperTrade(self.__exchange)
        self.__schedulers = []
        self.__variables = {}
        self.__hashes = []
        self.__assigned_websockets = []
    
    @property
    def variables(self):
        return self.__variables

    def modify_variable(self, callable, key, value):
        hashed = hash(callable)
        self.__variables[hashed][key] = value

    def add_price_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
                        init: typing.Callable = None, synced: bool = False, **kwargs):
        """
        Add Price Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. This
                can be used for accumulating price data
            synced: Sync the function to
        """
        self.__custom_price_event(callback, symbol, resolution, init, synced, kwargs=kwargs)

    def add_bar_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
                      init: typing.Callable = None, **kwargs):
        """
        Add Price Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. This
                can be used for accumulating price data
        """
        self.__custom_price_event(callback, symbol, resolution, init, synced=True, bar=True, kwargs=kwargs)

    def __custom_price_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
                             init: typing.Callable = None, synced: bool = False, bar: bool = False, **kwargs):
        """
        Add Price Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. This
                can be used for accumulating price data
            synced: Sync the function to
            bar: Get the OHLCV data for a valid exchange interval
        """
        resolution = time_interval_to_seconds(resolution)

        if bar:
            self.__scheduling_pair.append([symbol, resolution, 'bar'])
        else:
            self.__scheduling_pair.append([symbol, resolution, 'price_event'])
        callback_hash = hash((callback, hash((symbol, resolution))))
        if callback_hash in self.__hashes:
            raise ValueError("A callback of the same type and resolution has already been made for "
                             "the ticker: {}".format(symbol))
        else:
            self.__hashes.append(callback_hash)
        self.__variables[callback_hash] = AttributeDict({})
        state = StrategyState(self, self.__variables[callback_hash], resolution)

        # run init
        if init:
            init(symbol, state)

        if resolution < 10:
            # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
            self.Ticker_Manager.create_ticker(self.__idle_event, override_symbol=symbol)
            self.__schedulers.append(
                blankly.Scheduler(self.__price_event_websocket, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  resolution=resolution,
                                  variables=self.__variables[callback_hash],
                                  state_object=state,
                                  synced=synced,
                                  ohlc=bar,
                                  symbol=symbol, **kwargs)
            )
        else:
            # Use the API
            self.__schedulers.append(
                blankly.Scheduler(self.__price_event_rest, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  resolution=resolution,
                                  variables=self.__variables[callback_hash],
                                  state_object=state,
                                  synced=synced,
                                  ohlc=bar,
                                  symbol=symbol, **kwargs)
            )

    def __idle_event(self):
        """
        Function to skip & ignore callbacks
        """
        pass
        
    def __price_event_rest(self, **kwargs):
        callback = kwargs['callback']
        symbol = kwargs['symbol']
        resolution = kwargs['resolution']
        variables = kwargs['variables']
        ohlc = kwargs['ohlc']
        state = kwargs['state_object']  # type: StrategyState

        state.variables = variables
        state.resolution = resolution

        if ohlc:
            ohlcv_time = kwargs['ohlcv_time']
            while True:
                data = self.Interface.history(symbol, 1, resolution).iloc[-1].to_dict()
                if data['time'] + resolution == ohlcv_time:
                    break
                time.sleep(.5)
            data['price'] = self.Interface.get_price(symbol)
        else:
            data = self.Interface.get_price(symbol)

        callback(data, symbol, state)

    def __price_event_websocket(self, **kwargs):
        callback = kwargs['callback']
        symbol = kwargs['symbol']
        resolution = kwargs['resolution']
        variables = kwargs['variables']
        state = kwargs['state_object']  # type: StrategyState

        price = self.Ticker_Manager.get_most_recent_tick(override_symbol=symbol)

        state.variables = variables
        state.resolution = resolution

        callback(price, symbol, state)

    def __orderbook_event(self, tick, symbol, user_callback, state_object):
        user_callback(tick, symbol, state_object)

    def add_orderbook_event(self, callback: typing.Callable, symbol: str, init: typing.Callable = None,
                            **kwargs):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the orderbook for
            init: Callback function to allow a setup for the strategy variable. This
                can be used for accumulating price data
        """
        self.__scheduling_pair.append([symbol, 'live'])
        callback_hash = hash((callback, symbol))
        if callback_hash in self.__hashes:
            raise ValueError("A callback of the same type and resolution has already been made for the ticker: "
                             "{}".format(symbol))
        else:
            self.__hashes.append(callback_hash)
        self.__variables[callback_hash] = AttributeDict({})
        state = StrategyState(self, self.__variables[callback])
        if init:
            init(symbol, state)

        variables = self.__variables[callback_hash]

        # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
        self.Orderbook_Manager.create_orderbook(self.__orderbook_event, initially_stopped=True,
                                                override_symbol=symbol,
                                                symbol=symbol,
                                                user_callback=callback,
                                                variables=variables,
                                                state_object=state,
                                                **kwargs
                                                )

        exchange_type = self.__exchange.get_type()
        self.__assigned_websockets.append([symbol, exchange_type])

    def start(self):
        for i in self.__schedulers:
            i.start()

        for i in self.__assigned_websockets:
            self.Orderbook_Manager.restart_ticker(i[0], i[1])
    
    def backtest(self, 
                 initial_values: dict = None,
                 to: str = None,
                 start_date: str = None,
                 end_date: str = None,
                 save: bool = False,
                 settings_path: str = None,
                 callbacks: list = None,
                 **kwargs
                 ) -> BacktestResult:
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

                resample_account_value_for_metrics: str or bool = '1d' or False
                    Because backtest data can be input at a variety of resolutions, account value often needs to be
                        recalculated at consistent intervals for use in metrics & indicators.
                        This setting allows the specification of that consistent interval.
                        The value can be set to `False` to skip any recalculation.

                quote_account_value_in: str = 'USD'
                    Manually set what valuation should be used when calculating account value.
                        Multiple types of quote currency (ex: USD and EUR) are not supported because
                        there is no datasource for quoting pairs such as EUR-USD until forex integration.
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
                                                               asset_id=kwargs['symbol'],
                                                               time_interval=i.get_interval(),
                                                               state_object=kwargs['state_object'],
                                                               ohlc=kwargs['ohlc']
                                                               )

        # Run the backtest & return results
        results = backtesting_controller.run()

        # Clean up
        self.Interface = self.__interface_cache
        return results
