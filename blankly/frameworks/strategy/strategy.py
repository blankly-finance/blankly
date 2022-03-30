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

import time
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


class StrategyStructure(Model):
    def __init__(self, exchange: Exchange):
        super().__init__(exchange)

    def __rest_event(self, **kwargs):
        callback = kwargs['callback']  # type: callable
        symbol = kwargs['symbol']  # type: str
        resolution = kwargs['resolution']  # type: int
        variables = kwargs['variables']  # type: dict
        type_ = kwargs['type']  # type: EventType
        state = kwargs['state']  # type: StrategyState

        state.variables = variables
        state.resolution = resolution

        if type_ == EventType.bar_event:
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
            data['price'] = self.interface.get_price(symbol)
        else:
            data = self.interface.get_price(symbol)

        callback(data, symbol, state)

    def main(self, args):
        schedulers = args['schedulers']
        remote_backtesting = args['remote_backtesting']
        kwargs = []
        for scheduler in schedulers:
            kwargs = scheduler.get_kwargs()
        if self.is_backtesting:
            while self.has_data:
                pass
        else:
            if remote_backtesting:
                warnings.warn("Aborted attempt to start a live strategy a backtest configuration")
                return
            for i in events:
                kwargs = i.get_kwargs()
                if kwargs['init'] is not None:
                    kwargs['init'](kwargs['symbol'], kwargs['state_object'])
                i.start()


class Strategy(StrategyBase):
    __exchange: Exchange
    interface: ABCExchangeInterface

    def __init__(self, exchange: Exchange):
        super().__init__(exchange, StrategyLogger(exchange.get_interface(), strategy=self))
        self._paper_trade_exchange = blankly.PaperTrade(self.__exchange)
        self.model = Model(exchange)

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
        for scheduler in self.schedulers:
            for event_element in scheduler.get_kwargs():
                self.model.backtester.add_prices(to=to,
                                                 start_date=start_date,
                                                 stop_date=end_date,
                                                 symbol=event_element['symbol'],
                                                 resolution=event_element['resolution'])
        self.model.backtest(args={
            'schedulers': self.schedulers,
            'remote_backtesting': self.remote_backtesting
        })
        pass

    def time(self) -> float:
        if self.backtesting_controller is not None and self.backtesting_controller.time is not None:
            return self.backtesting_controller.time
        else:
            return time.time()
