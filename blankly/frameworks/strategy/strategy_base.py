"""
    Abstraction for creating interval driven user strategies
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
import threading
import time
import typing
import warnings

import pandas as pd

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.paper_trade.backtest_controller import BackTestController
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.frameworks.strategy.strategy_state import StrategyState
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import AttributeDict, info_print
from blankly.utils.utils import get_ohlcv_from_list
from blankly.exchanges.strategy_logger import StrategyLogger


class Strategy:
    def __init__(self, exchange: Exchange, currency_pair='BTC-USD'):
        """
        Create a new strategy object. A strategy can be used to run your code live while be backtestable and modular
         across exchanges.

        Function Signatures:
        init(symbol: str, state: blankly.StrategyState)
        price_event(price: float, symbol: str, state: blankly.StrategyState)
        orderbook_event(tick: dict, symbol: str, state: blankly.StrategyState)
        bar_event(bar: dict, symbol: str, state: blankly.StrategyState)
        teardown(blankly.StrategyState)
        """
        self.__remote_backtesting = blankly._backtesting
        self.__exchange = exchange
        self.ticker_manager = blankly.TickerManager(self.__exchange.get_type(), currency_pair)
        self.orderbook_manager = blankly.OrderbookManager(self.__exchange.get_type(), currency_pair)

        self.__scheduling_pair = []  # Object to hold a currency and the resolution its pulled at: ["BTC-USD", 60]
        self.interface = StrategyLogger(interface=exchange.get_interface(), strategy=self)

        # Create a cache for the current interface, and a wrapped paper trade object for user backtesting
        self.__interface_cache = self.interface
        self.__paper_trade_exchange = blankly.PaperTrade(self.__exchange)
        self.__schedulers = []
        self.__variables = {}
        self.__hashes = []
        self.__orderbook_websockets = []
        self.__ticker_websockets = []

        # Initialize backtesting attributes. This only used for sending times to the Strategy/StrategyState
        # This is done because we switch the interface to a paper trade interface
        self.backtesting_controller = None

        # This will throw a warning if they're trying to use an orderbook in the backtest
        self.__using_orderbook = False

        # Attempt to report the strategy
        blankly.reporter.export_strategy(self)

        # Create a lock for the teardown so nothing happens while its going on
        self.lock = threading.Lock()

        # This will be updated when the teardown() function completes
        self.torndown = False

    @property
    def variables(self):
        return self.__variables

    def modify_variable(self, callable_: typing.Callable, key, value):
        hashed = hash(callable_)
        self.__variables[hashed][key] = value

    def add_price_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
                        init: typing.Callable = None, teardown: typing.Callable = None, synced: bool = False,
                        variables: dict = None):
        """
        Add Price Event. This will provide you with an updated price every time the callback is run
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. Example usages include
                downloading price data before usage
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful
            synced: Sync the function to
            variables: A dictionary to initialize the state's internal values
        """
        self.__custom_price_event(callback, symbol, resolution, init, synced, teardown=teardown, variables=variables)

    def add_bar_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
                      init: typing.Callable = None, teardown: typing.Callable = None, variables: dict = None):
        """
        The bar event sends a dictionary of {open, high, low, close, volume} which has occurred in the interval.
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. Example usages include
                downloading price data before usage
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful
            variables: A dictionary to initialize the state's internal values
        """
        self.__custom_price_event(callback, symbol, resolution, init, synced=True, bar=True, teardown=teardown,
                                  variables=variables)

    def __custom_price_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
                             init: typing.Callable = None, synced: bool = False, bar: bool = False,
                             teardown: typing.Callable = None, variables: dict = None):
        """
        Add Price Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. Example usages include
                downloading price data before usage
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful
            synced: Sync the function to
            bar: Get the OHLCV data for a valid exchange interval
        """
        # Make sure variables is always an empty dictionary if None
        if variables is None:
            variables = {}

        resolution = time_interval_to_seconds(resolution)

        if bar:
            self.__scheduling_pair.append([symbol, resolution, 'bar'])
        else:
            self.__scheduling_pair.append([symbol, resolution, 'price_event'])

        variables_ = AttributeDict(variables)
        state = StrategyState(self, variables_, symbol, resolution=resolution)

        if resolution < 60:
            # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
            self.ticker_manager.create_ticker(self.__idle_event, override_symbol=symbol)
            self.__schedulers.append(
                blankly.Scheduler(self.__price_event_websocket, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  resolution=resolution,
                                  variables=variables_,
                                  state_object=state,
                                  synced=synced,
                                  init=init,
                                  teardown=teardown,
                                  ohlc=bar,
                                  symbol=symbol)
            )
            exchange_type = self.__exchange.get_type()
            self.__ticker_websockets.append([symbol, exchange_type, init, state, teardown])
        else:
            # Use the API
            self.__schedulers.append(
                blankly.Scheduler(self.__price_event_rest, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  resolution=resolution,
                                  variables=variables_,
                                  state_object=state,
                                  synced=synced,
                                  ohlc=bar,
                                  init=init,
                                  teardown=teardown,
                                  symbol=symbol)
            )

    def __idle_event(self, *args, **kwargs):
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
                # Sometimes coinbase doesn't download recent data correctly
                try:
                    data = self.interface.history(symbol=symbol, to=1, resolution=resolution).iloc[-1].to_dict()
                    if data['time'] + resolution == ohlcv_time:
                        break
                except IndexError:
                    pass
                time.sleep(.5)
            data['price'] = self.interface.get_price(symbol)
        else:
            data = self.interface.get_price(symbol)

        callback(data, symbol, state)

    def __price_event_websocket(self, **kwargs):
        callback = kwargs['callback']
        symbol = kwargs['symbol']
        resolution = kwargs['resolution']
        variables = kwargs['variables']
        ohlc = kwargs['ohlc']
        state = kwargs['state_object']  # type: StrategyState

        if ohlc:
            close_time = kwargs['ohlcv_time']
            open_time = close_time-resolution
            ticker_feed = list(reversed(self.ticker_manager.get_feed(override_symbol=symbol)))
            #     tick        tick
            #      |    ohlcv close                            ohlcv open
            # 0    |   -20          -40            -60        -80
            # newest, newest - 1, newest - 2
            count = 0
            while ticker_feed[count]['time'] > close_time:
                count += 1

            close_index = count

            # Start at the close index to save some iterations
            count = close_index
            while ticker_feed[count]['time'] < open_time:
                count += 1
            # Subtract 1 to put it back inside the range
            count -= 1
            open_index = count

            # Get the latest price that isn't past the timeframe
            last_price = ticker_feed[close_index:][-1]['price']

            data = get_ohlcv_from_list(list(reversed(ticker_feed[close_index:open_index])), last_price)

        else:
            try:
                data = self.ticker_manager.get_most_recent_tick(override_symbol=symbol)['price']
            except TypeError:
                info_print("No valid data yet - using rest.")
                data = self.interface.get_price(symbol)

        state.variables = variables
        state.resolution = resolution

        callback(data, symbol, state)

    @staticmethod
    def __orderbook_event(tick, symbol, user_callback, state_object):
        user_callback(tick, symbol, state_object)

    def add_orderbook_event(self, callback: typing.Callable, symbol: str, init: typing.Callable = None,
                            teardown: typing.Callable = None, variables: dict = None):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the orderbook for
            init: Callback function to allow a setup for the strategy variable. This
                can be used for accumulating price data
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful:
            variables: A dictionary to initialize the state's internal values
        """
        # Make sure variables is always an empty dictionary if None
        if variables is None:
            variables = {}
        self.__scheduling_pair.append([symbol, None])
        callback_hash = hash((callback, symbol))
        if callback_hash in self.__hashes:
            raise ValueError("A callback of the same type and resolution has already been made for the ticker: "
                             "{}".format(symbol))
        else:
            self.__hashes.append(callback_hash)
        self.__variables[callback_hash] = AttributeDict(variables)
        state = StrategyState(self, self.__variables[callback_hash], symbol=symbol)

        variables = self.__variables[callback_hash]

        # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
        self.orderbook_manager.create_orderbook(self.__orderbook_event, initially_stopped=True,
                                                override_symbol=symbol,
                                                symbol=symbol,
                                                user_callback=callback,
                                                variables=variables,
                                                state_object=state)

        exchange_type = self.__exchange.get_type()
        self.__orderbook_websockets.append([symbol, exchange_type, init, state, teardown])

        # Set this to true so that we can throw a warning in the backtest
        self.__using_orderbook = True

    def start(self):
        """
        Run your model live!

        Simply call this function to take your strategy configuration live on your exchange
        """
        if self.__remote_backtesting:
            warnings.warn("Aborted attempt to start a live strategy a backtest configuration")
            return
        for i in self.__schedulers:
            kwargs = i.get_kwargs()
            if kwargs['init'] is not None:
                kwargs['init'](kwargs['symbol'], kwargs['state_object'])
            i.start()

        for i in self.__orderbook_websockets:
            # Index 2 contains the initialization function for the assigned websockets array
            if i[2] is not None:
                i[2](i[0], i[3])
            self.orderbook_manager.restart_ticker(i[0], i[1])

        for i in self.__ticker_websockets:
            # The initialization function should have already been called for ticker websockets
            # Notice this is different from orderbook websockets because these are put into the scheduler
            self.ticker_manager.restart_ticker(i[0], i[1])

    def teardown(self):
        self.lock.acquire()
        for i in self.__schedulers:
            i.stop_scheduler()
            kwargs = i.get_kwargs()
            teardown = kwargs['teardown']
            state_object = kwargs['state_object']
            if callable(teardown):
                teardown(state_object)

        for i in self.__orderbook_websockets:
            self.orderbook_manager.close_websocket(override_symbol=i[0], override_exchange=i[1])
            # Call the stored teardown
            teardown_func = i[4]
            if callable(teardown_func):
                teardown_func(i[3])

        for i in self.__ticker_websockets:
            self.ticker_manager.close_websocket(override_symbol=i[0], override_exchange=i[1])
        self.lock.release()

        # Show that all teardowns have finished
        self.torndown = True

    def time(self) -> float:
        if self.backtesting_controller is not None and self.backtesting_controller.time is not None:
            return self.backtesting_controller.time
        else:
            return time.time()

    def backtest(self,
                 to: str = None,
                 initial_values: dict = None,
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

            to (str): Declare an amount of time before now to backtest from: ex: '5y' or '10h'
            initial_values (dict): Dictionary of initial value sizes (i.e { 'BTC': 3, 'USD': 5650}).
                Using this will override the values that are currently on your exchange.
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

                continuous_caching: bool
                    Utilize the advanced price caching system built into the backtest. Automatically aggregate and prune
                    downloaded data.

                resample_account_value_for_metrics: str or bool = '1d' or False
                    Because backtest data can be input at a variety of resolutions, account value often needs to be
                        recalculated at consistent intervals for use in metrics & indicators.
                        This setting allows the specification of that consistent interval.
                        The value can be set to `False` to skip any recalculation.

                quote_account_value_in: str = 'USD'
                    Manually set what valuation should be used when calculating account value.
                        Multiple types of quote currency (ex: USD and EUR) are not supported because
                        there is no datasource for quoting pairs such as EUR-USD until forex integration.

                ignore_user_exceptions: bool = True
                    Set this to True to handle user exceptions identically to how they're handled by strategy calls.
                        False means that the backtest will immediately stop & attempt to generate a report if something
                        in the user calls goes wrong. True will replicate strategy errors.

                risk_free_return_rate: float = 0.0
                    Set this to be the theoretical rate of return with no risk
        """

        start = None
        end = None

        # Even if they specified start/end unevenly it will be overwritten with any to argument
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

        # If start/ends are specified unevenly
        if (start_date is None and end_date is not None) or (start_date is not None and end_date is None):
            raise ValueError("Both start and end dates must be set or use the 'to' argument.")

        self.interface = self.__paper_trade_exchange.get_interface()
        self.backtesting_controller = BackTestController(self.__paper_trade_exchange,
                                                         backtest_settings_path=settings_path,
                                                         callbacks=callbacks
                                                         )

        # Write any kwargs as settings to the settings - save if enabled.
        for k, v in kwargs.items():
            self.backtesting_controller.write_setting(k, v, save)

        if initial_values is not None:
            self.backtesting_controller.write_initial_price_values(initial_values)

        # Write each scheduling pair as a price event - save if enabled.
        if start is not None and end is not None:
            for i in self.__scheduling_pair:
                # None means live which is orderbook, which we skip anyway
                if i[1] is not None:
                    self.backtesting_controller.add_prices(i[0], start, end, i[1], save=save)
        else:
            info_print("User-specified start and end time not given. Defaulting to using only cached data.")

        if self.__using_orderbook:
            warning_string = "Artificial orderbook generation is not yet supported for backtesting - " \
                             "skipping orderbook callbacks."
            warnings.warn(warning_string)

        # Append each of the events the class defines into the backtest
        for i in self.__schedulers:
            kwargs = i.get_kwargs()
            self.backtesting_controller.append_backtest_price_event(callback=kwargs['callback'],
                                                                    asset_id=kwargs['symbol'],
                                                                    time_interval=i.get_interval(),
                                                                    state_object=kwargs['state_object'],
                                                                    ohlc=kwargs['ohlc'],
                                                                    init=kwargs['init'],
                                                                    teardown=kwargs['teardown']
                                                                    )

        # Run the backtest & return results
        results = self.backtesting_controller.run()

        blankly.reporter.export_backtest_result(results)

        # Clean up
        self.interface = self.__interface_cache
        return results
