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
from blankly.exchanges.abc_base_exchange import ABCBaseExchange
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.interfaces.paper_trade.backtest_controller import BackTestController
from blankly.exchanges.abc_exchange import ABCExchange
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.frameworks.strategy.strategy_state import StrategyState
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import AttributeDict, info_print
from blankly.utils.utils import get_ohlcv_from_list
from blankly.exchanges.strategy_logger import StrategyLogger


# TODO this entire class needs to be fixed it's all fucked
class StrategyBase:
    _exchange: ABCBaseExchange
    interface: ABCBaseExchangeInterface

    def __init__(self, exchange, interface):
        """
        Create a new strategy object. A strategy can be used to run your code live while be backtestable and modular
         across exchanges.
         Args:
             exchange: An exchange object. This can be created by doing something similar to exchange = blankly.Alpaca()

        Function Signatures:
        init(symbol: str, state: blankly.StrategyState)
        price_event(price: float, symbol: str, state: blankly.StrategyState)
        orderbook_event(tick: dict, symbol: str, state: blankly.StrategyState)
        bar_event(bar: dict, symbol: str, state: blankly.StrategyState)
        teardown(blankly.StrategyState)
        """
        self._remote_backtesting = blankly._backtesting
        self._exchange = exchange
        self.interface = interface

        self.ticker_manager = blankly.TickerManager(self._exchange.get_type(), '')
        self.orderbook_manager = blankly.OrderbookManager(self._exchange.get_type(), '')

        self._scheduling_pair = []  # Object to hold a currency and the resolution it's pulled at: ["BTC-USD", 60]

        # Create a cache for the current interface
        self._interface_cache = self.interface
        self._schedulers = []
        self.__variables = {}
        self._hashes = []
        self._orderbook_websockets = []
        self._ticker_websockets = []

        # Initialize backtesting attributes. This only used for sending times to the Strategy/StrategyState
        # This is done because we switch the interface to a paper trade interface
        self.backtesting_controller = None

        # This will throw a warning if they're trying to use an orderbook in the backtest
        self._using_orderbook = False

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

    # # TODO these could have some parameters assigned by a super class
    # def add_arbitrage_event(self, callback: typing.Callable, symbols: list, resolution: typing.Union[str, float],
    #                         init: typing.Callable = None, teardown: typing.Callable = None, synced: bool = False,
    #                         variables: dict = None):
    #     """
    #     Add Arbitrage Event - This allows periodic events where prices are gathered asynchronously. When run live at a
    #      small interval, this allows minimal latency when gathering the price of the requested symbols.
    #     """

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
        self.__custom_price_event(callback=callback, symbol=symbol, resolution=resolution, init=init, synced=synced,
                                  teardown=teardown, variables=variables, type_='price_event')

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
        self.__custom_price_event(type_='bar', synced=True, bar=True, callback=callback, symbol=symbol,
                                  resolution=resolution, init=init, teardown=teardown, variables=variables)

    def __custom_price_event(self,
                             type_: str,
                             callback: typing.Callable = None,
                             symbol: str = None,
                             resolution: typing.Union[str, float] = None,
                             init: typing.Callable = None,
                             synced: bool = False,
                             bar: bool = False,
                             teardown: typing.Callable = None, variables: dict = None):
        """
        Add Price Event
        Args:
            type_: The type of event that the price event refers to
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. Example usages include
                downloading price data before usage
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful
            synced: Sync the function to
            bar: Get the OHLCV data for a valid exchange interval
            variables: Initial dictionary to write into the state variable
        """
        # Make sure variables is always an empty dictionary if None
        if variables is None:
            variables = {}
        resolution = time_interval_to_seconds(resolution)

        self._scheduling_pair.append([symbol, resolution, type_])

        variables_ = AttributeDict(variables)
        state = StrategyState(self, variables_, symbol, resolution=resolution)

        if resolution < 60:
            # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
            self.ticker_manager.create_ticker(self.__idle_event, override_symbol=symbol)
            self._schedulers.append(
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
            exchange_type = self._exchange.get_type()
            self._ticker_websockets.append([symbol, exchange_type, init, state, teardown])
        else:
            # Use the API
            self._schedulers.append(
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

        # Export a new symbol to the backend
        blankly.reporter.export_used_symbol(symbol)

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
                    if self.interface.get_exchange_type() == "alpaca":
                        break
                    else:
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
        self._scheduling_pair.append([symbol, None])
        callback_hash = hash((callback, symbol))
        if callback_hash in self._hashes:
            raise ValueError("A callback of the same type and resolution has already been made for the ticker: "
                             "{}".format(symbol))
        else:
            self._hashes.append(callback_hash)
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

        exchange_type = self._exchange.get_type()
        self._orderbook_websockets.append([symbol, exchange_type, init, state, teardown])

        # Set this to true so that we can throw a warning in the backtest
        self._using_orderbook = True

    def start(self):
        """
        Run your model live!

        Simply call this function to take your strategy configuration live on your exchange
        """
        if self._remote_backtesting:
            warnings.warn("Aborted attempt to start a live strategy a backtest configuration")
            return
        for i in self._schedulers:
            kwargs = i.get_kwargs()
            if kwargs['init'] is not None:
                kwargs['init'](kwargs['symbol'], kwargs['state_object'])
            i.start()

        for i in self._orderbook_websockets:
            # Index 2 contains the initialization function for the assigned websockets array
            if i[2] is not None:
                i[2](i[0], i[3])
            self.orderbook_manager.restart_ticker(i[0], i[1])

        for i in self._ticker_websockets:
            # The initialization function should have already been called for ticker websockets
            # Notice this is different from orderbook websockets because these are put into the scheduler
            self.ticker_manager.restart_ticker(i[0], i[1])

    def teardown(self):
        self.lock.acquire()
        for i in self._schedulers:
            i.stop_scheduler()
            kwargs = i.get_kwargs()
            teardown = kwargs['teardown']
            state_object = kwargs['state_object']
            if callable(teardown):
                teardown(state_object)

        for i in self._orderbook_websockets:
            self.orderbook_manager.close_websocket(override_symbol=i[0], override_exchange=i[1])
            # Call the stored teardown
            teardown_func = i[4]
            if callable(teardown_func):
                teardown_func(i[3])

        for i in self._ticker_websockets:
            self.ticker_manager.close_websocket(override_symbol=i[0], override_exchange=i[1])
        self.lock.release()

        # Show that all teardowns have finished
        self.torndown = True

    def time(self) -> float:
        raise NotImplementedError

    def backtest(self,
                 to: str = None,
                 initial_values: dict = None,
                 start_date: typing.Union[str, float, int] = None,
                 end_date: typing.Union[str, float, int] = None,
                 save: bool = False,
                 settings_path: str = None,
                 callbacks: list = None,
                 **kwargs
                 ) -> BacktestResult:
        raise NotImplementedError

