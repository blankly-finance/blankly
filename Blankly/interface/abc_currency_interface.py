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
    def start_paper_trade_watchdog(self):
        """
        Start the internal order watching loop
        """
        pass

    @abc.abstractmethod
    def __paper_trade_watchdog(self):
        """
        Internal order watching system
        """
        pass

    @abc.abstractmethod
    def __evaluate_paper_trade(self, order, current_price):
        """
        This calculates fees & evaluates accurate value
        Args:
            order (dict): Order dictionary to derive the order attributes
            current_price (float): The current price of the currency pair the limit order was created on
        """
        pass

    @abc.abstractmethod
    def __init_exchange__(self):
        pass

    @abc.abstractmethod
    def __override_paper_trading(self, value):
        self.__paper_trading = bool(value)

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
             The exchange's direct calls object. A Blankly Bot class should have immediate access to this by
             default

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
    def get_account(self, currency=None, override_paper_trading=False):
        """
        Get all currencies in an account, or sort by currency/account_id
        Args:
            currency (Optional): Filter by particular currency
            override_paper_trading (Optional bool): If paper trading is enabled, setting this to true will get the
             actual account values

            These arguments are mutually exclusive

        TODO add return example
        """
        pass

    @abc.abstractmethod
    def market_order(self, product_id, side, funds) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            product_id: currency to buy
            side: buy/sell
            funds: desired amount of quote currency to use
        """
        pass

    @abc.abstractmethod
    def limit_order(self, product_id, side, price, size) -> LimitOrder:
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
    def cancel_order(self, currency_id, order_id) -> dict:
        """
        Cancel an order on a particular currency id & order id

        Args:
            currency_id: This is the currency id that the order is under
            order_id: The unique ID of the order.

        TODO add return example
        """

    @abc.abstractmethod
    def get_open_orders(self, product_id=None):
        """
        List open orders.
        Args:
            product_id (optional) (str): Currency pair such as BTC-USD
        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_order(self, currency_id, order_id) -> dict:
        """
        Get a certain order
        Args:
            currency_id: This is the currency id that the order is under
            order_id: The unique ID of the order.
        TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_fees(self):
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
    def get_product_history(self, product_id, epoch_start, epoch_stop, granularity):
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
    def get_market_limits(self, product_id):
        """
        Find order limits for the exchange
        Args:
            product_id: Blankly product ID format (BTC-USD)
            TODO add return example
        """
        pass

    @abc.abstractmethod
    def get_price(self, currency_pair) -> float:
        """
        Returns just the price of a currency pair.
        Args:
            currency_pair: Blankly product ID ex: BTC-USD
            TODO add return example
        """
        pass
