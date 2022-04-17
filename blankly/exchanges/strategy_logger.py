"""
    Logging system to allow users to view & understand actions done in the strategy
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

import pandas
from typing import Union
from datetime import datetime as dt

import blankly
from blankly.exchanges.interfaces.abc_exchange_interface import ABCExchangeInterface
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.utils.utils import AttributeDict


class StrategyLogger(ABCExchangeInterface):
    def __init__(self, interface=None, strategy=None):
        self.interface = interface
        self.strategy = strategy
        self.__type = self.interface.get_exchange_type()

    def get_calls(self):
        """
        No logging implemented
        """
        return self.interface.get_calls()
    
    def get_exchange_type(self):
        """
        No logging implemented
        """
        return self.interface.get_exchange_type()
    
    def get_account(self, symbol: str = None) -> AttributeDict:
        """
        No logging implemented
        """
        return self.interface.get_account(symbol)

    """
    These next three queries have large responses. It is unclear if this quantity of data is useful or necessary
    """
    def get_products(self):
        """
        No logging implemented
        """
        return self.interface.get_products()

    def get_product_history(self, symbol: str, epoch_start: float,
                            epoch_stop: float, resolution: Union[str, int]) -> pandas.DataFrame:
        """
        No logging implemented
        """
        return self.interface.get_product_history(symbol, epoch_start, epoch_stop, resolution)
    
    def history(self,
                symbol: str,
                to: Union[str, int] = 200,
                resolution: Union[str, int] = '1d',
                start_date: Union[str, dt, float] = None,
                end_date: Union[str, dt, float] = None,
                return_as: str = 'df') -> pandas.DataFrame:
        """
        No logging implemented
        """
        return self.interface.history(symbol, to=to,
                                      resolution=resolution, start_date=start_date,
                                      end_date=end_date, return_as=return_as)
    
    def market_order(self, symbol: str, side: str, size: float) -> MarketOrder:
        out = self.interface.market_order(symbol, side, size)

        # Record this market order along with the arguments
        try:
            blankly.reporter.log_market_order({
                'symbol': symbol,
                'exchange': self.__type,
                'size': size,
                'id': out.get_id(),
                'side': side
            }, self.__type)
        except Exception:
            pass
        return out
    
    def limit_order(self, symbol: str, side: str, price: float, size: float) -> LimitOrder:
        out = self.interface.limit_order(symbol, side, price, size)

        # Record limit order along with the arguments
        try:
            blankly.reporter.log_limit_order({
                'symbol': symbol,
                'exchange': self.__type,
                'size': size,
                'id': out.get_id(),
                'side': side,
                'price': price
            }, self.__type)
        except Exception:
            pass
        return out
    
    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        No logging implemented
        """
        return self.interface.cancel_order(symbol, order_id)

    def get_open_orders(self, symbol: str = None) -> list:
        """
        No logging implemented
        """
        return self.interface.get_open_orders(symbol=symbol)

    def get_order(self, symbol: str, order_id: str) -> dict:
        """
        TODO - this needs to update the order on the backend
        """
        out = self.interface.get_order(symbol, order_id)

        # Record the arguments
        try:
            blankly.reporter.update_order({
                'id': order_id,
                'status': out['status']
            }, self.__type)
        except Exception:
            pass
        return out

    def get_fees(self, symbol) -> dict:
        """
        No logging implemented
        """
        return self.interface.get_fees(symbol)

    def get_order_filter(self, symbol: str):
        """
        No logging implemented
        """
        return self.interface.get_order_filter(symbol)
    
    def get_price(self, symbol: str) -> float:
        """
        No logging implemented
        """
        return self.interface.get_price(symbol)

    """
    No logging implemented for these properties
    """
    @property
    def account(self) -> AttributeDict:
        """
        No logging implemented
        """
        return self.interface.account
    
    @property
    def orders(self) -> list:
        """
        No logging implemented
        """
        return self.interface.orders

    @property
    def cash(self) -> float:
        """
        No logging implemented
        """
        return self.interface.cash
    
