"""
This is a commentated but cleaner implementation of strategy_base.py

Largely this project is going on the backburner
"""

# """
#     Abstraction for creating interval driven user strategies
#     Copyright (C) 2021  Emerson Dove, Brandon Fan
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Lesser General Public License as published
#     by the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
# """
#
# import datetime
# import threading
# import time
# import typing
# import warnings
#
# import pandas as pd
#
# import blankly
# from blankly.exchanges.exchange import Exchange
# from blankly.exchanges.interfaces.paper_trade.backtest_controller import BackTestController
# from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
# from blankly.frameworks.strategy.strategy_state import StrategyState
# from blankly.utils.time_builder import time_interval_to_seconds
# from blankly.utils.utils import AttributeDict, info_print
# from blankly.utils.utils import get_ohlcv_from_list
# from blankly.exchanges.strategy_logger import StrategyLogger
#
#
# class Strategy:
#     def __init__(self, exchange: Exchange):
#         """
#         Create a new strategy object. A strategy can be used to run your code live while be backtestable and modular
#          across exchanges.
#          Args:
#              exchange: An exchange object. This can be created by doing something similar to exchange = blankly.Alpaca()
#
#         Function Signatures:
#         init(symbol: str, state: blankly.StrategyState)
#         price_event(price: float, symbol: str, state: blankly.StrategyState)
#         orderbook_event(tick: dict, symbol: str, state: blankly.StrategyState)
#         bar_event(bar: dict, symbol: str, state: blankly.StrategyState)
#         teardown(blankly.StrategyState)
#         """
#         self.__exchange = exchange
#         self.__backtest_scheduler: dict = {}
#
#         self.interface = StrategyLogger(interface=exchange.get_interface(), strategy=self)
#
#         self.__schedulers = []
#
#         self.ticker_manager = blankly.TickerManager(self.__exchange.get_type(), '')
#
#     def __idle_event(self, *args, **kwargs):
#         """
#         Function to skip & ignore callbacks. Mainly used for websockets
#         """
#         pass
#
#     def add_price_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
#                         init: typing.Callable = None, teardown: typing.Callable = None, synced: bool = False,
#                         variables: dict = None):
#         """
#         Add Price Event. This will provide you with an updated price every time the callback is run
#         Args:
#             callback: The price event callback that will be added to the current ticker and run at the proper resolution
#             symbol: Currency pair to create the price event for
#             resolution: The resolution that the callback will be run - in seconds
#             init: Callback function to allow a setup for the strategy variable. Example usages include
#                 downloading price data before usage
#             teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
#                 positions, writing or cleaning up data or anything else useful
#             synced: Sync the function to
#             variables: A dictionary to initialize the state's internal values
#         """
#         self.__custom_price_event(callback=callback, symbol=symbol, resolution=resolution, init=init, synced=synced,
#                                   teardown=teardown, variables=variables, type_='price_event')
#
#     def add_bar_event(self, callback: typing.Callable, symbol: str, resolution: typing.Union[str, float],
#                       init: typing.Callable = None, teardown: typing.Callable = None, variables: dict = None):
#         """
#         The bar event sends a dictionary of {open, high, low, close, volume} which has occurred in the interval.
#         Args:
#             callback: The price event callback that will be added to the current ticker and run at the proper resolution
#             symbol: Currency pair to create the price event for
#             resolution: The resolution that the callback will be run - in seconds
#             init: Callback function to allow a setup for the strategy variable. Example usages include
#                 downloading price data before usage
#             teardown: A function to run when the strategy is stopped or interrupted. Example usages include liquidating
#                 positions, writing or cleaning up data or anything else useful
#             variables: A dictionary to initialize the state's internal values
#         """
#         self.__custom_price_event(type_='bar', synced=True, bar=True, callback=callback, symbol=symbol,
#                                   resolution=resolution, init=init, teardown=teardown, variables=variables)
#
#     def __custom_price_event(self,
#                              type_: str,
#                              callback: typing.Callable = None,
#                              symbol: str = None,
#                              resolution: typing.Union[str, float] = None,
#                              init: typing.Callable = None,
#                              synced: bool = False,
#                              bar: bool = False,
#                              teardown: typing.Callable = None, variables: dict = None):
#         """
#         Add Price Event
#         Args:
#             type_: The type of event that the price event refers to
#             callback: The price event callback that will be added to the current ticker and run at the proper
#              resolution
#             symbol: Currency pair to create the price event for
#             resolution: The resolution that the callback will be run - in seconds
#             init: Callback function to allow a setup for the strategy variable. Example usages include
#                 downloading price data before usage
#             teardown: A function to run when the strategy is stopped or interrupted. Example usages include
#              liquidating
#                 positions, writing or cleaning up data or anything else useful
#             synced: Sync the function to
#             bar: Get the OHLCV data for a valid exchange interval
#             variables: Initial dictionary to write into the state variable
#         """
#         # Make sure variables is always an empty dictionary if None
#         if variables is None:
#             variables = {}
#
#         resolution = time_interval_to_seconds(resolution)
#
#         # Make sure the type is always added to the price events
#         if type_ not in self.__backtest_scheduler:
#             self.__backtest_scheduler[type_] = []
#
#         self.__backtest_scheduler[type_] = {
#             'symbol': symbol,
#             'resolution': resolution
#         }
#
#         variables_ = AttributeDict(variables)
#         state = StrategyState(self, variables_, symbol, resolution=resolution)
#
#         scheduler_kwargs = {
#             'initially_stopped': True,
#             'callback': callback,
#             'resolution': resolution,
#             'variables': variables_,
#             'state_object': state,
#             'synced': synced,
#             'init': init,
#             'teardown': teardown,
#             'ohlc': bar,
#             'symbol': symbol
#         }
#
#         if resolution < 10:
#             self.ticker_manager.create_ticker(self.__idle_event, override_symbol=symbol)
#             self.__schedulers.append(
#                 blankly.Scheduler(self.__price_event_websocket, resolution,
#                                   **scheduler_kwargs)
#             )
#             exchange_type = self.__exchange.get_type()
#
#     def __price_event_rest(self, **kwargs):
#         callback = kwargs['callback']
#         symbol = kwargs['symbol']
#         resolution = kwargs['resolution']
#         variables = kwargs['variables']
#         ohlc = kwargs['ohlc']
#         state = kwargs['state_object']  # type: StrategyState
#
#         state.variables = variables
#         state.resolution = resolution
#
#         if ohlc:
#             ohlcv_time = kwargs['ohlcv_time']
#             while True:
#                 # Sometimes coinbase doesn't download recent data correctly
#                 try:
#                     data = self.interface.history(symbol=symbol, to=1, resolution=resolution).iloc[-1].to_dict()
#                     if data['time'] + resolution == ohlcv_time:
#                         break
#                 except IndexError:
#                     pass
#                 time.sleep(.5)
#             data['price'] = self.interface.get_price(symbol)
#         else:
#             data = self.interface.get_price(symbol)
#
#     def __price_event_websocket(self, **kwargs):
#         callback = kwargs['callback']
#         symbol = kwargs['symbol']
#         resolution = kwargs['resolution']
#         variables = kwargs['variables']
#         ohlc = kwargs['ohlc']
#         state = kwargs['state_object']  # type: StrategyState
#
#         if ohlc:
#             close_time = kwargs['ohlcv_time']
#             open_time = close_time-resolution
#             ticker_feed = list(reversed(self.ticker_manager.get_feed(override_symbol=symbol)))
#             #     tick        tick
#             #      |    ohlcv close                            ohlcv open
#             # 0    |   -20          -40            -60        -80
#             # newest, newest - 1, newest - 2
#             count = 0
#             while ticker_feed[count]['time'] > close_time:
#                 count += 1
#
#             close_index = count
#
#             # Start at the close index to save some iterations
#             count = close_index
#             while ticker_feed[count]['time'] < open_time:
#                 count += 1
#             # Subtract 1 to put it back inside the range
#             count -= 1
#             open_index = count
#
#             # Get the latest price that isn't past the timeframe
#             last_price = ticker_feed[close_index:][-1]['price']
#
#             data = get_ohlcv_from_list(list(reversed(ticker_feed[close_index:open_index])), last_price)
#
#         else:
#             try:
#                 data = self.ticker_manager.get_most_recent_tick(override_symbol=symbol)['price']
#             except TypeError:
#                 info_print("No valid data yet - using rest.")
#                 data = self.interface.get_price(symbol)
#
#         state.variables = variables
#         state.resolution = resolution
#
#         callback(data, symbol, state)
