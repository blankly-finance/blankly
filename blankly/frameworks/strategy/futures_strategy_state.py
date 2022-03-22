"""
    Strategy State for FuturesStrategy objects.
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
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.utils.utils import AttributeDict, get_base_asset, get_quote_asset, pretty_print_json
from blankly.frameworks.strategy.futures_strategy import FuturesStrategy


class FuturesStrategyState:
    strategy: FuturesStrategy
    interface: FuturesExchangeInterface
    variables: AttributeDict
    resolution: int
    symbol: str
    base_asset: str
    quote_asset: str

    def __init__(self,
                 strategy,
                 variables: AttributeDict,
                 symbol,
                 resolution: [int, float] = None):
        self.strategy = strategy
        self.variables = variables
        self.resolution = resolution
        self.symbol = symbol
        self.base_asset = get_base_asset(symbol)
        self.quote_asset = get_quote_asset(symbol)

    @property
    def interface(self) -> FuturesExchangeInterface:
        return self.strategy.interface

    @property
    def time(self) -> float:
        return self.strategy.time()

    def __str__(self):
        return f"""Symbol: {self.symbol}
Time: {self.time}
Resolution: {self.resolution}
Variables:
{pretty_print_json(self.variables, actually_print=False)}
"""
