"""
    Logic to provide consistency across exchanges
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

import abc
from datetime import datetime as dt
from typing import Union

import pandas

from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.utils.utils import AttributeDict
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder


class ABCExchangeInterface(ABCBaseExchangeInterface, abc.ABC):
    @abc.abstractmethod
    def __init__(self, exchange_name, authenticated_API):
        """
        Create an abstract exchange interface
        Args:
            exchange_name (str): Define exchange name ex: 'binance' or 'coinbase_pro'
            authenticated_API (obj): Authenticated direct calls object
        """
        pass

    @abc.abstractmethod
    def get_calls(self):
        """
        Get the direct & authenticated exchange object

        Returns:
             The exchange's direct calls object. A blankly Bot class should have immediate access to this by
             default
        """
        pass

    @abc.abstractmethod
    def get_exchange_type(self):
        """
        Get the type of exchange ex: "coinbase_pro" or "binance"

        Returns:
             A string that corresponds to the type of exchange

        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_products(self) -> list:
        """
        Get all trading pairs on the exchange & some information about the exchange limits.

        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_account(self,
                    symbol: str = None) -> AttributeDict:
        """
        Get all assets in an account, or sort by symbol/account_id
        Args:
            symbol (Optional): Filter by particular symbol

            These arguments are mutually exclusive

        TODO add return example
        """
        pass

    @abc.abstractmethod
    def market_order(self,
                     symbol: str,
                     side: str,
                     size: float) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            symbol: asset to buy
            side: buy/sell
            size: desired amount of base asset to use
        """
        pass

    @abc.abstractmethod
    def limit_order(self,
                    symbol: str,
                    side: str,
                    price: float,
                    size: float) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            symbol: asset to buy
            side: buy/sell
            price: price to set limit order
            size: amount of asset (like BTC) for the limit to be valued
        """
        pass

    @abc.abstractmethod
    def cancel_order(self,
                     symbol: str,
                     order_id: str) -> dict:
        """
        Cancel an order on a particular symbol & order id

        Args:
            symbol: This is the asset id that the order is under
            order_id: The unique ID of the order.

        TODO add return example
        """

    @abc.abstractmethod
    def get_open_orders(self,
                        symbol: str = None) -> list:
        """
        List open orders.
        Args:
            symbol (optional) (str): Asset such as BTC-USD
        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_order(self,
                  symbol: str,
                  order_id: str) -> dict:
        """
        Get a certain order
        Args:
            symbol: Asset that the order is under
            order_id: The unique ID of the order.
        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_fees(self, symbol: str) -> dict:
        """
        Get market fees
        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_order_filter(self,
                         symbol: str) -> dict:
        """
        Find order limits for the exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_price(self,
                  symbol: str) -> float:
        """
        Returns just the price of a symbol.
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            TODO add return example
        """
        pass

    @property
    @abc.abstractmethod
    def account(self) -> AttributeDict:
        """
        Get all assets in an account, or sort by assets/account_id

        TODO add return example
        """
        pass

    @property
    @abc.abstractmethod
    def orders(self) -> list:
        """
        List open orders.
        TODO add return example
        """
        pass

    @property
    @abc.abstractmethod
    def cash(self) -> float:
        """
        Get the amount of cash in a portfolio. The cash default is set in the settings .json file
        """
        pass
