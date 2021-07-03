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
from Blankly.utils.purchases.limit_order import LimitOrder
from Blankly.utils.purchases.market_order import MarketOrder
import pandas
from typing import Union


class ICurrencyInterface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, exchange_name, authenticated_API):
        """
        Create a currency interface
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
             The exchange's direct calls object. A Blankly Bot class should have immediate access to this by
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
    def get_products(self):
        """
        Get all trading pairs on the exchange & some information about the exchange limits.

        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_account(self,
                    currency: str = None) -> dict:
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency (Optional): Filter by particular currency

            These arguments are mutually exclusive

        TODO add return example
        """
        pass

    @abc.abstractmethod
    def market_order(self,
                     product_id: str,
                     side: str,
                     funds: float) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            product_id: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
        """
        pass

    @abc.abstractmethod
    def limit_order(self,
                    product_id: str,
                    side: str,
                    price: float,
                    size: float) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            product_id: currency to buy
            side: buy/sell
            price: price to set limit order
            size: amount of currency (like BTC) for the limit to be valued
        """
        pass

    @abc.abstractmethod
    def cancel_order(self,
                     currency_id: str,
                     order_id: str) -> dict:
        """
        Cancel an order on a particular currency id & order id

        Args:
            currency_id: This is the currency id that the order is under
            order_id: The unique ID of the order.

        TODO add return example
        """

    @property
    @abc.abstractmethod
    def account(self) -> dict:
        """
        Get all currencies in an account, or sort by currency/account_id

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
    def cash(self) -> dict:
        """
        Get the amount of cash in a portfolio. The cash default is set in the settings .json file
        """
        pass

    @abc.abstractmethod
    def get_open_orders(self,
                        product_id: str = None) -> list:
        """
        List open orders.
        Args:
            product_id (optional) (str): Currency pair such as BTC-USD
        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_order(self,
                  currency_id: str,
                  order_id: str) -> dict:
        """
        Get a certain order
        Args:
            currency_id: This is the currency id that the order is under
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
    Binance: 
        get_deposit_history
        get_withdraw_history

    """
    @abc.abstractmethod
    def history(self,
                product_id: str,
                to: Union[str, int, float],
                granularity: Union[str, float]) -> pandas.DataFrame:
        """
        Wrapper for .get_product_history() which allows users to more easily get product history from right now.
        Args:
            product_id: Blankly product ID format (BTC-USD)
            to (str or number): The amount of time before now to get product history
            granularity: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
            TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_product_history(self,
                            product_id: str,
                            epoch_start: float,
                            epoch_stop: float,
                            granularity: Union[str, float]) -> pandas.DataFrame:
        """
        Returns the product history from an exchange
        Args:
            product_id: Blankly product ID format (BTC-USD)
            epoch_start: Time to begin download
            epoch_stop: Time to stop download
            granularity: Resolution in seconds between tick (ex: 60 = 1 per minute)
        Returns:
            Dataframe with *at least* 'time (epoch)', 'low', 'high', 'open', 'close', 'volume' as columns.
            TODO add return example
        """

    @abc.abstractmethod
    def get_market_limits(self,
                          product_id: str):
        """
        Find order limits for the exchange
        Args:
            product_id: Blankly product ID format (BTC-USD)
            TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_price(self,
                  currency_pair: str) -> float:
        """
        Returns just the price of a currency pair.
        Args:
            currency_pair: Blankly product ID ex: BTC-USD
            TODO add return example
        """
        pass
