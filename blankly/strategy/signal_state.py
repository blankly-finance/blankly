"""
    A similar state management to StrategyState but optimized for evaluation & reporting
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

from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface as Interface
from blankly.utils.utils import AttributeDict, format_with_new_line


class SignalState:
    interface: Interface
    variables: AttributeDict
    symbols: list

    def __init__(self, signal):
        """
        This is a SignalState object - a simplified version of StrategyState

        Args:
            signal: Construct with a signal object to allow interaction
        """

        self.signal = signal
        self.variables = AttributeDict({})
        self.symbols = signal.symbols
        self.resolution = signal.resolution

    @property
    def interface(self) -> Interface:
        """
        Get the interface object to interact with the exchange
        """
        return self.signal.interface

    @property
    def time(self) -> float:
        """
        Get the current time. This will only the current time because it is not in a backtesting framework
        """
        return time.time()

    def notify(self, message=None) -> None:
        """
        Send the formatted results as an email
        """
        self.signal.notify(message)

    def __str__(self):
        output = ""
        output = format_with_new_line(output, 'Time: ', self.time)
        output = format_with_new_line(output, 'Symbols: ', self.symbols)
        return format_with_new_line(output, 'Variables: ', self.variables)
