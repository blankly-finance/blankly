"""
    Logging system to allow users to view & understand actions done in the strategy
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
from abc import ABC

from blankly.enums import Side
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface

# TODO
from blankly.exchanges.orders.futures.futures_order import FuturesOrder


class FuturesStrategyLogger:
    interface: FuturesExchangeInterface

    def __init__(self, interface=None, strategy=None):
        self.interface = interface
        self.strategy = strategy

    def __getattribute__(self, item):
        # run the overridden function in this class if it exists, or default to the method in self.interface
        try:
            # this is NOT recursive, it will get the *actual* attribute
            return object.__getattribute__(self, item)
        except AttributeError:
            return self.interface.__getattribute__(item)

    # TODO log order (and other order types)
    # example:
    def market_order(self, symbol: str, side: Side, size: float, *args,
                     **kwargs) -> FuturesOrder:
        # log here
        return self.interface.market_order(symbol, side, size, *args, **kwargs)
