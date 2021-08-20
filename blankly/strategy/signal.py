"""
    Signal management system for starting & stopping long term monitoring
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

from typing import List
from blankly.exchanges.exchange import Exchange


class Signal:
    def __init__(self, exchange: Exchange,
                 evaluator: typing.Callable,
                 symbols: List[str],
                 init: typing.Callable = None,
                 teardown: typing.Callable = None,
                 formatter: typing.Callable = None):
        """
        Create a new signal.

        This heavily differs from Strategy objects. While a Strategy is optimized for the implementation of
         short or long-term trading strategies, a Signal is optimized for long-term monitoring & reporting of many
         symbols. Signals are designed to be scheduled to run over intervals of days & weeks. When deployed live,
         a signal-based script will only start when scheduled, then exit entirely.

        Args:
            exchange: An exchange object to construct the signal on
            evaluator: The function that can take information about a signal & classify that signal based on parameters
            symbols: A list of symbols to run on.
            init: Optional setup code to run when the program starts
            teardown: Optional teardown code to run before the program finishes
            formatter: Optional formatting function that pretties the results form the evaluator
        """
        self.exchange = exchange
        self.symbols = symbols
        self.__callables = {
            'evaluator': evaluator,
            'init': init,
            'teardown': teardown,
            'formatter': formatter
        }
        self.interface = exchange.interface
