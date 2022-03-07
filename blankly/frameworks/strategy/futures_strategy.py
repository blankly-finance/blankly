"""
    Abstraction for creating interval driven user strategies for trading futures.
    Copyright (C) 2022 Matias Kotlik

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

import typing

from blankly.exchanges.futures.futures_exchange import FuturesExchange
from blankly.exchanges.futures.futures_strategy_logger import FuturesStrategyLogger
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.interfaces.paper_trade.backtest_result import BacktestResult
from blankly.frameworks.strategy.strategy_base import StrategyBase


class FuturesStrategy(StrategyBase):
    exchange: FuturesExchange
    interface: FuturesExchangeInterface

    def __init__(self, exchange: FuturesExchange):
        super().__init__(
            exchange, FuturesStrategyLogger(exchange.interface, strategy=self))

    def backtest(self,
                 to: str = None,
                 initial_values: dict = None,
                 start_date: typing.Union[str, float, int] = None,
                 end_date: typing.Union[str, float, int] = None,
                 save: bool = False,
                 settings_path: str = None,
                 callbacks: list = None,
                 **kwargs) -> BacktestResult:
        raise NotImplementedError

    def time(self) -> float:
        """
        Return the current time, or backtesting time if we are backtesting.
        """
        raise NotImplementedError
