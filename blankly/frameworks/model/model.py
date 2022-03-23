"""
    An improved strategy simulation layer built for spot and futures trading
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
import typing

from blankly.exchanges.interfaces.paper_trade.backtest_controller import BackTestController, BacktestResult
from blankly.exchanges.interfaces.paper_trade.paper_trade import PaperTrade
from blankly.exchanges.exchange import Exchange
import time


class Model:
    def __init__(self, exchange: Exchange):
        self.__exchange = exchange
        self.backtesting = False
        # Backtest engine pushes this
        self.backtesting_time = None

        self.exchange = exchange
        self.interface = exchange.interface

        self.backtester = BackTestController(PaperTrade(self.__exchange), self)

    def backtest(self, args) -> BacktestResult:
        # Construct the backtest controller
        if not isinstance(self.__exchange, Exchange):
            raise NotImplementedError

        return self.backtester.run(args)

    def run(self, args: typing.Any = None):
        pass

    def main(self, args):
        raise NotImplementedError("Add a main function to your strategy to run the model.")

    @property
    def time(self):
        if not self.backtesting:
            return time.time()
        else:
            return self.backtesting_time

    def sleep(self, seconds: [int, float]):
        if not self.backtesting:
            time.sleep(seconds)
