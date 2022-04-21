"""
    Spot specific class for strategy
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
import threading
import time
import traceback
import typing
import warnings

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.exchanges.strategy_logger import StrategyLogger
from blankly.frameworks.model.model import Model
from blankly.frameworks.strategy.strategy_base import StrategyBase, EventType
from blankly.frameworks.strategy import StrategyState
from blankly.utils.utils import info_print


class StrategyStructure(Model):
    def __init__(self, exchange: Exchange):
        self.lock = threading.Lock()
        super().__init__(exchange)

        self.orderbook_websockets = None
        self.ticker_websockets = None
        self.ticker_manager = None
        self.orderbook_manager = None
        self.schedulers = None
        self.remote_backtesting = None

    def construct_strategy(self, schedulers, orderbook_websockets,
                           ticker_websockets, orderbook_manager, ticker_manager):
        self.schedulers = schedulers
        self.orderbook_websockets = orderbook_websockets
        self.ticker_websockets = ticker_websockets
        self.orderbook_manager = orderbook_manager
        self.ticker_manager = ticker_manager

    def rest_event(self, **kwargs):
        callback = kwargs['callback']  # type: callable
        symbol = kwargs['symbol']  # type: str
        resolution = kwargs['resolution']  # type: int
        variables = kwargs['variables']  # type: dict
        type_ = kwargs['type']  # type: EventType
        state = kwargs['state']  # type: StrategyState

        state.variables = variables
        state.resolution = resolution

        if type_ == EventType.bar_event:
            if not self.is_backtesting:
                bar_time = kwargs['bar_time']
                while True:
                    # Sometimes coinbase doesn't download recent data correctly
                    try:
                        data = self.interface.history(symbol=symbol, to=1, resolution=resolution).iloc[-1].to_dict()
                        if self.interface.get_exchange_type() == "alpaca":
                            break
                        else:
                            if data['time'] + resolution == bar_time:
                                break
                    except IndexError:
                        pass
                    time.sleep(.5)
            else:
                # If we are backtesting always just grab the last point and hope for the best of course
                try:
                    data = self.interface.history(symbol=symbol, to=1, resolution=resolution).iloc[-1].to_dict()
                except IndexError:
                    warnings.warn("No bar found for this time range")
                    return
            args = [data, symbol, state]
        elif type_ == EventType.price_event:
            data = self.interface.get_price(symbol)
            args = [data, symbol, state]
        elif type_ == EventType.scheduled_event:
            args = [state]
        elif type_ == EventType.arbitrage_event:
            prices = {}
            # If we're backtesting loop through the symbol and just grab the price
            if self.is_backtesting:
                for sym in symbol:
                    prices[sym] = self.interface.get_price(sym)

            # We have to be a bit more strategy if we're live
            else:
                def grab_price(threaded_symbol):
                    prices[threaded_symbol] = self.interface.get_price(threaded_symbol)

                threadpool = []
                for sym in symbol:
                    threadpool.append(threading.Thread(target=grab_price, args=(sym,)))

                # Start the threads
                for thread in threadpool:
                    thread.start()

                # Join each of the threads because they've writen to the symbol
                for thread in threadpool:
                    thread.join()
            args = [prices, symbol, state]
        else:
            return

        try:
            callback(*args)
        except Exception:
            traceback.print_exc()

    def run_price_events(self, kwargs_list: list):
        for events_definition in kwargs_list:
            events_definition['next_run'] = self.backtester.initial_time
        while self.has_data:
            kwargs_list = sorted(kwargs_list, key=lambda d: d['next_run'])
            next_event = kwargs_list[0]

            # Sleep the difference
            self.sleep(next_event['next_run'] - self.time)

            # Run the event
            self.rest_event(**next_event)

            # Value the account after each run
            self.backtester.value_account()
            kwargs_list[0]['next_run'] += kwargs_list[0]['resolution']

    def main(self, args):
        if self.is_backtesting:
            self.run_backtest()
        else:
            self.run_live()

    def run_backtest(self):
        # Write in the new interface, no matter which type it is
        for scheduler in self.schedulers:
            kwargs = scheduler.get_kwargs()
            # Overwrite the internal interface in the created strategy
            kwargs['state'].strategy.interface = self.interface
        self.__run_init()

        kwargs_list = []
        for scheduler in self.schedulers:
            kwargs_list.append(scheduler.get_kwargs())

        self.run_price_events(kwargs_list)

    def __run_init(self):
        # Switch to live mode for the inits
        if self.is_backtesting:
            self.interface.backtesting = False
        for i in self.schedulers:
            kwargs = i.get_kwargs()
            if kwargs['init'] is not None:
                if kwargs['type'] != EventType.scheduled_event:
                    kwargs['init'](kwargs['symbol'], kwargs['state'])
                else:
                    kwargs['init'](kwargs['state'])

        # Switch back to the backtesting status
        self.interface.backtesting = self.is_backtesting

    def run_live(self):
        self.__run_init()

        for scheduler in self.schedulers:
            scheduler.start()

        for i in self.orderbook_websockets:
            # Index 2 contains the initialization function for the assigned websockets array
            if i[2] is not None:
                i[2](i[0], i[3])
            self.orderbook_manager.restart_ticker(i[0], i[1])

        for i in self.ticker_websockets:
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

        for i in self.orderbook_websockets:
            self.orderbook_manager.close_websocket(override_symbol=i[0], override_exchange=i[1])
            # Call the stored teardown
            teardown_func = i[4]
            if callable(teardown_func):
                teardown_func(i[3])

        for i in self.ticker_websockets:
            self.ticker_manager.close_websocket(override_symbol=i[0], override_exchange=i[1])
        self.lock.release()


class Strategy(StrategyBase):
    __exchange: Exchange
    interface: ABCExchangeInterface

    def __init__(self, exchange: Exchange):
        self.model = StrategyStructure(exchange)
        super().__init__(exchange, StrategyLogger(exchange.get_interface(), strategy=self), model=self.model)
        self._paper_trade_exchange = blankly.PaperTrade(exchange)
        self.__prices_added = False

    def backtest(self,
                 to: str = None,
                 initial_values: dict = None,
                 start_date: typing.Union[str, float, int] = None,
                 end_date: typing.Union[str, float, int] = None,
                 settings_path: str = None,
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
            start_date (str): Override argument "to" by specifying a start date such as "03/06/2018". This can also
                be an epoch time as a float or int.
            end_date (str): End the backtest at a date such as "03/06/2018". This can also be an epoch type as a float
                or int
            settings_path (str): Path to the backtest.json file.

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
        self.setup_model()
        if len(self.orderbook_websockets) != 0 or len(self.ticker_websockets) != 0:
            info_print("Found websocket events added to this strategy. These are not yet backtestable without "
                       "event based data")

        self.__add_prices(to, start_date, end_date)
        return self.model.backtest(args={}, initial_values=initial_values, settings_path=settings_path, kwargs=kwargs)

    def __add_prices(self, to, start_date, end_date):
        for scheduler in self.schedulers:
            event_element = scheduler.get_kwargs()

            # Skip any scheduled events
            if event_element['symbol'] is None:
                continue

            # Loop through the symbols if it is a list
            if isinstance(event_element['symbol'], list):
                for symbol in event_element['symbol']:
                    self.model.backtester.add_prices(to=to,
                                                     start_date=start_date,
                                                     stop_date=end_date,
                                                     symbol=symbol,
                                                     resolution=event_element['resolution'])
            else:
                self.model.backtester.add_prices(to=to,
                                                 start_date=start_date,
                                                 stop_date=end_date,
                                                 symbol=event_element['symbol'],
                                                 resolution=event_element['resolution'])

            self.__prices_added = True

        if not self.__prices_added:
            raise LookupError("No prices added. If using scheduled events, create an empty price event or add prices"
                              " manually using strategy.add_prices()")

    def add_prices(self, symbol: str, resolution: [str, int, float], to: str = None,
                   start_date: typing.Union[str, float, int] = None,
                   stop_date: typing.Union[str, float, int] = None):
        """
        Directly add prices to the strategy
        """
        self.model.backtester.add_prices(symbol, resolution, to, start_date, stop_date)
        self.__prices_added = True

    def setup_model(self):
        self.model.construct_strategy(self.schedulers, self.orderbook_websockets,
                                      self.ticker_websockets, self.orderbook_manager,
                                      self.ticker_manager)

    def start(self):
        """
        Run your model live!

        Simply call this function to take your strategy configuration live on your exchange
        """
        self.setup_model()
        if self.remote_backtesting:
            warnings.warn("Aborted attempt to start a live strategy a backtest configuration")
            return
        self.model.run()

    def time(self) -> float:
        return self.model.time
