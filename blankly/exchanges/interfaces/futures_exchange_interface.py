"""
    Base class for FuturesExchangeInterfaces.
    Provides common functionality for Futures Exchanges.
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

import abc

import blankly.utils.utils as utils
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.orders.futures.futures_limit_order import FuturesLimitOrder
from blankly.exchanges.orders.futures.futures_market_order import FuturesMarketOrder


class FuturesExchangeInterface(ABCBaseExchangeInterface, abc.ABC):
    exchange_name: str

    needed = {
        'product': [["symbol", str], ["base_asset", str], ["quote_asset", str],
                    ["base_min_size", float], ["base_max_size", float],
                    ["base_increment", float]],
        'account': [
            ["available", float],
        ],
        'order': [["status", str], ["symbol", str], ["id", str],
                  ["created_at", float], ["funds", float], ["type", str],
                  ["contract_type", str], ["side", str], ["position", str],
                  ["price", float], ["time_in_force", str],
                  ["stop_price", float]],
    }

    def __init__(self,
                 exchange_name,
                 authenticated_api,
                 preferences_path=None):
        self.exchange_name = exchange_name
        self.calls = authenticated_api

        self.user_preferences = utils.load_user_preferences(preferences_path)

        self.exchange_properties = None
        self.available_currencies = {}

        if self.user_preferences['settings']['test_connectivity_on_auth']:
            self.init_exchange()

    def get_exchange_type(self) -> str:
        """Returns the exchange type (ex. 'binance', 'coinbase', 'alpaca')"""
        return self.exchange_name

    @abc.abstractmethod
    def init_exchange(self):
        """Initializes the exchange"""
        # this should usually set self.available_currencies
        pass

    @abc.abstractmethod
    def get_products(self) -> list:
        """Returns a list of all products traded on this exchange"""
        pass

    @abc.abstractmethod
    def get_account(self, symbol: str = None) -> utils.AttributeDict:
        """Returns account information, or information for only one `symbol` if one is given."""
        pass

    @abc.abstractmethod
    def market_order(self, symbol: str, side: str, size: float,
                     position: str) -> FuturesMarketOrder:
        """Places a market order"""
        pass

    @abc.abstractmethod
    def limit_order(self, symbol: str, side: str, price: float, size: float,
                    position: str) -> FuturesLimitOrder:
        """Places a limit order"""
        pass

    # TODO maybe? it's not even implemented for spot trading
    # def stop_limit_order(self, symbol: str, side: str, price: float,
    #                      stop_price: float, size: float,
    #                      position: str) -> FuturesLimitOrder:
    #     """Places a stop-limit order"""
    #     raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancels an order"""
        pass

    @abc.abstractmethod
    def close_position(self, symbol: str = None):
        """Closes open positions"""
        pass

    @abc.abstractmethod
    def get_open_orders(self, symbol: str = None) -> list:
        """Returns all currently open orders, filtered by `symbol` if one is provided."""
        pass

    @abc.abstractmethod
    def get_order(self, order_id: str) -> dict:
        """Returns information for the order corresponding to `order_id`"""
        pass

    @abc.abstractmethod
    def get_price(self, symbol: str) -> float:
        """Returns the current price of an asset"""
        pass

    @property
    def account(self) -> utils.AttributeDict:
        """Account information"""
        return self.get_account()

    @property
    def orders(self) -> list:
        """All currently open orders"""
        return self.get_open_orders()

    @property
    def cash(self) -> float:
        """The amount of cash in a portfolio. The currency for 'cash' is set in settings.json"""
        pass
