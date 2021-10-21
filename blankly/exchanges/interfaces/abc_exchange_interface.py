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

from blankly.utils.utils import AttributeDict
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder


class ABCExchangeInterface(abc.ABC):
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
    def get_fees(self) -> dict:
        """
        Get market fees
        TODO add return example
        """
        pass

    """
    Coinbase Pro: get_account_history
    binance: 
        get_deposit_history
        get_withdraw_history

    """

    @abc.abstractmethod
    def history(self,
                symbol: str,
                to: Union[str, int] = 200,
                resolution: Union[str, int] = '1d',
                start_date: Union[str, dt, float] = None,
                end_date: Union[str, dt, float] = None,
                return_as: str = 'df') -> pandas.DataFrame:
        """
        Wrapper for .get_product_history() which allows users to more easily get product history from right now.
        Args:
            symbol: Blankly product ID format (BTC-USD)
            to (str or int): The number of data points back in time either expressed as a string
                ("1y" meaning 1 year back") or int of points (300 points at specified resolution)
            resolution: Resolution as a string (i.e. "1d", "4h", "1y")
            start_date (str or datetime or float): Start Date for data gathering (in either string, datetime or epoch
                timestamp)
            end_date (str or datetime or float): End Date for data gathering (in either string, datetime or epoch
                timestamp)
            return_as (str): Return Type (Either list or df (dataframe))
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
            TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_product_history(self,
                            symbol: str,
                            epoch_start: float,
                            epoch_stop: float,
                            resolution: Union[str, int]) -> pandas.DataFrame:
        """
        Returns the product history from an exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            resolution: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
            TODO add return example
        """

    @abc.abstractmethod
    def get_order_filter(self,
                         symbol: str):
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
