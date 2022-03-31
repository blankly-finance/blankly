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

import threading
import typing
import warnings
import enum


import blankly
from blankly.exchanges.abc_base_exchange import ABCBaseExchange
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.frameworks.strategy.strategy_state import StrategyState
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import AttributeDict


class EventType(enum.Enum):
    price_event = 'price_event'
    bar_event = 'bar_event'
    scheduled_event = 'scheduled_event'
    arbitrage_event = 'arbitrage_event'
    orderbook_event = "orderbook_event"


# TODO this entire class needs to be fixed it's all fucked
class StrategyBase:
    __exchange: ABCBaseExchange
    interface: ABCBaseExchangeInterface

    def __init__(self, exchange: ABCBaseExchange, interface: ABCBaseExchangeInterface):
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
        self.remote_backtesting = blankly._backtesting
        self.__exchange = exchange
        self.interface = interface

        self.ticker_manager = blankly.TickerManager(self.__exchange.get_type(), '')
        self.orderbook_manager = blankly.OrderbookManager(self.__exchange.get_type(), '')

        # Attempt to report the strategy
        blankly.reporter.export_strategy(self)

        # Create a lock for the teardown so nothing happens while it's going on
        self.lock = threading.Lock()

        # This will be updated when the teardown() function completes
        self.torndown = False

        self.schedulers = []

        self.interface = interface

        self.__orderbook_websockets = []
        self.__ticker_websockets = []

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
                                  teardown=teardown, variables=variables, type_=EventType.price_event)

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
        self.__custom_price_event(type_=EventType.bar_event, synced=True, callback=callback, symbol=symbol,
                                  resolution=resolution, init=init, teardown=teardown, variables=variables)

    def __custom_price_event(self,
                             type_: EventType,
                             callback: typing.Callable = None,
                             symbol: str = None,
                             resolution: typing.Union[str, float] = None,
                             init: typing.Callable = None,
                             synced: bool = False,
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

        variables_ = AttributeDict(variables)
        state = StrategyState(self, variables_, symbol, resolution=resolution)

        # Use the API
        self.schedulers.append(
            blankly.Scheduler(self.__price_event_rest, resolution,
                              initially_stopped=True,
                              synced=synced,
                              callback=callback,
                              resolution=resolution,
                              variables=variables_,
                              state=state,
                              type=type_,
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
        raise NotImplementedError

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

        state = StrategyState(self, AttributeDict(variables), symbol=symbol)

        # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
        self.orderbook_manager.create_orderbook(self.__orderbook_event, initially_stopped=True,
                                                override_symbol=symbol,
                                                symbol=symbol,
                                                user_callback=callback,
                                                variables=variables,
                                                state=state)

        exchange_type = self.__exchange.get_type()
        self.__orderbook_websockets.append([symbol, exchange_type, init, state, teardown])

    def start(self):
        """
        Run your model live!

        Simply call this function to take your strategy configuration live on your exchange
        """
        if self.remote_backtesting:
            warnings.warn("Aborted attempt to start a live strategy a backtest configuration")
            return
        for i in self.schedulers:
            kwargs = i.get_kwargs()
            if kwargs['init'] is not None:
                kwargs['init'](kwargs['symbol'], kwargs['state'])
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
        for i in self.schedulers:
            i.stop_scheduler()
            kwargs = i.get_kwargs()
            teardown = kwargs['teardown']
            state_object = kwargs['state']
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
        raise NotImplementedError

    def backtest(self,
                 to: str = None,
                 initial_values: dict = None,
                 start_date: typing.Union[str, float, int] = None,
                 end_date: typing.Union[str, float, int] = None,
                 settings_path: str = None,
                 **kwargs
                 ) -> BacktestResult:
        raise NotImplementedError
