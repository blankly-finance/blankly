"""
    Class to pass in the current Strategy State
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

from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface as Interface
from blankly.utils.utils import AttributeDict, get_base_asset, get_quote_asset, format_with_new_line, pretty_print_json


class StrategyState:
    interface: Interface
    variables: AttributeDict
    resolution: int

    """Strategy State"""
    def __init__(self, strategy, variables: AttributeDict, symbol, resolution: [int, float] = None):
        self.strategy = strategy
        self.variables = variables
        self.resolution = resolution
        self.symbol = symbol

        # Base & quotes are conditionally defined
        self.base_asset = None
        self.quote_asset = None
        if isinstance(symbol, str):
            self.base_asset = get_base_asset(symbol)
            self.quote_asset = get_quote_asset(symbol)

    @staticmethod
    def append_bar(history_reference, new_bar: dict):
        history_reference['open'].append(new_bar['open'])
        history_reference['high'].append(new_bar['high'])
        history_reference['low'].append(new_bar['low'])
        history_reference['close'].append(new_bar['close'])
        history_reference['volume'].append(new_bar['volume'])
        history_reference['time'].append(new_bar['time'])

    @property
    def interface(self) -> Interface:
        """
        Get the interface object that the strategy is running on. Use this to interact with your exchange.
        """
        return self.strategy.interface

    @property
    def time(self) -> float:
        """
        Get the time from the strategy.
        This will automatically switch to match the correct times during backtesting
        """
        return self.strategy.time()

    def __str__(self):
        output = ""
        output = format_with_new_line(output, "Symbol: ", self.symbol)

        output = format_with_new_line(output, "Time: ", self.time)

        output = format_with_new_line(output, "Resolution: ", self.resolution)

        output = format_with_new_line(output, "Variables: ")

        output = format_with_new_line(output, pretty_print_json(self.variables, actually_print=False))

        return output

    @property
    def vars(self):
        """
        An alias to the variables attribute
        """
        return self.variables