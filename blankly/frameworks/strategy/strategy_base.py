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


class StrategyBase:
    __exchange: ABCBaseExchange
    interface: ABCBaseExchangeInterface

    def __init__(self, exchange: ABCBaseExchange, interface: ABCBaseExchangeInterface, model):
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

        self.orderbook_websockets = []
        self.ticker_websockets = []
        self.model = model

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

    def add_scheduled_event(self, callback: typing.Callable, resolution: typing.Union[str, float],
                            init: typing.Callable = None, teardown: typing.Callable = None,
                            synced: bool = False, variables: dict = None):
        """
        Add a scheduled event. This will call the callback at the rate defined in the resolution

        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. Example usages include
                downloading price data before usage
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful
            synced: Sync the function to
            variables: A dictionary to initialize the state's internal values
        """
        self.__custom_price_event(callback=callback, symbol=None, resolution=resolution, init=init, synced=synced,
                                  teardown=teardown, variables=variables, type_=EventType.scheduled_event)

    def add_arbitrage_event(self, callback: typing.Callable, symbols: list, resolution: typing.Union[str, float],
                            init: typing.Callable = None, teardown: typing.Callable = None, synced: bool = False,
                            variables: dict = None):
        """
        Add Price Event. This will provide you with an updated price every time the callback is run
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbols: A list of symbols to get data for
            resolution: The resolution that the callback will be run - in seconds
            init: Callback function to allow a setup for the strategy variable. Example usages include
                downloading price data before usage
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful
            synced: Sync the function to
            variables: A dictionary to initialize the state's internal values
        """
        self.__custom_price_event(callback=callback, symbol=symbols, resolution=resolution, init=init, synced=synced,
                                  teardown=teardown, variables=variables, type_=EventType.arbitrage_event)

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
                             symbol: [str, list] = None,
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
            blankly.Scheduler(self.model.rest_event, resolution,
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

    @staticmethod
    def __websocket_callback(tick, symbol, user_callback, state_object):
        user_callback(tick, symbol, state_object)

    def add_tick_event(self, callback: callable, symbol: str, init: callable = None, teardown: callable = None,
                       variables: dict = None):
        """
        Add a tick event - This will call the callback everytime the exchange provides a change in the price due to a
         trade occurring
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            symbol: Currency pair to create the orderbook for
            init: Callback function to allow a setup for the strategy variable. This
                can be used for accumulating price data
            teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
                positions, writing or cleaning up data or anything else useful:
            variables: A dictionary to initialize the state's internal values
        """
        if variables is None:
            variables = {}

        state = StrategyState(self, AttributeDict(variables), symbol=symbol)

        self.ticker_manager.create_ticker(self.__websocket_callback, initially_stopped=True,
                                          override_symbol=symbol,
                                          symbol=symbol,
                                          user_callback=callback,
                                          variables=variables,
                                          state=state)

        self.ticker_websockets.append([symbol, self.__exchange.get_type(), init, state, teardown])

    def add_orderbook_event(self, callback: callable, symbol: str, init: typing.Callable = None,
                            teardown: typing.Callable = None, variables: dict = None):
        """
        Add Orderbook Event - This will call the given callback everytime the exchange provides a change in the
         orderbook
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
        self.orderbook_manager.create_orderbook(self.__websocket_callback, initially_stopped=True,
                                                override_symbol=symbol,
                                                symbol=symbol,
                                                user_callback=callback,
                                                variables=variables,
                                                state=state)

        self.ticker_websockets.append([symbol, self.__exchange.get_type(), init, state, teardown])

    def start(self):
        """
        Run your model live!

        Simply call this function to take your strategy configuration live on your exchange
        """
        raise NotImplementedError

    def teardown(self):
        raise NotImplementedError

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
