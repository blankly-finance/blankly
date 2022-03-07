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

from blankly.enums import PositionMode, Side
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_limit_order import FuturesLimitOrder
from blankly.exchanges.orders.futures.futures_market_order import FuturesMarketOrder


# TODO
class FuturesStrategyLogger:
    interface: FuturesExchangeInterface
    strategy: 'FuturesStrategy'

    def __init__(self, interface=None, strategy=None):
        self.interface = interface
        self.strategy = strategy

    def __getattribute__(self, item):
        # run the overidden function in this class if it exists, or default to the method in self.interface
        try:
            # this is NOT recursive, it will get the *actual* attribute
            return object.__getattribute__(self, item)
        except AttributeError:
            return self.interface.__getattribute__(item)

    def market_order(
            self,
            symbol: str,
            side: Side,
            size: float,
            position: PositionMode = PositionMode.BOTH) -> FuturesMarketOrder:
        # TODO log order
        return self.interface.market_order(symbol, side, size, position)

    def limit_order(
            self,
            symbol: str,
            side: Side,
            price: float,
            size: float,
            position: PositionMode = PositionMode.BOTH) -> FuturesLimitOrder:
        # TODO log order
        return self.interface.limit_order(symbol, side, price, size, position)
