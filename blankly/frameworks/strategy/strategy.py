import datetime
import time
import typing
import warnings

import pandas as pd

import blankly
from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.paper_trade.backtest_controller import BackTestController
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.exchanges.strategy_logger import StrategyLogger
from blankly.frameworks.strategy import StrategyBase
from blankly.utils.time_builder import time_interval_to_seconds
from blankly.utils.utils import info_print


class Strategy(StrategyBase):
    _exchange: Exchange

    def __init__(self, exchange: Exchange):
        super().__init__(exchange, StrategyLogger(exchange.get_interface(), strategy=self))
        self._paper_trade_exchange = blankly.PaperTrade(self._exchange)

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

        start = None
        end = None

        # Even if they specified start/end unevenly it will be overwritten with any to argument
        if to is not None:
            start = time.time() - time_interval_to_seconds(to)
            end = time.time()

        if start_date is not None:
            if isinstance(end_date, (int, float)):
                start = start_date
            else:
                start_date = pd.to_datetime(start_date)
                epoch = datetime.datetime.utcfromtimestamp(0)
                start = (start_date - epoch).total_seconds()

        if end_date is not None:
            if isinstance(end_date, (int, float)):
                end = end_date
            else:
                end_date = pd.to_datetime(end_date)
                epoch = datetime.datetime.utcfromtimestamp(0)
                end = (end_date - epoch).total_seconds()

        # If start/ends are specified unevenly
        if (start_date is None and end_date is not None) or (start_date is not None and end_date is None):
            raise ValueError("Both start and end dates must be set or use the 'to' argument.")

        self.interface = self._paper_trade_exchange.get_interface()
        self.backtesting_controller = BackTestController(self._paper_trade_exchange,
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
            for i in self._scheduling_pair:
                # None means live which is orderbook, which we skip anyway
                if i[1] is not None:
                    self.backtesting_controller.add_prices(i[0], start, end, i[1], save=save)
        else:
            info_print("User-specified start and end time not given. Defaulting to using only cached data.")

        if self._using_orderbook:
            warning_string = "Artificial orderbook generation is not yet supported for backtesting - " \
                             "skipping orderbook callbacks."
            warnings.warn(warning_string)

        # Append each of the events the class defines into the backtest
        for i in self._schedulers:
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
        self.interface = self._interface_cache
        return results

    def time(self) -> float:
        if self.backtesting_controller is not None and self.backtesting_controller.time is not None:
            return self.backtesting_controller.time
        else:
            return time.time()
