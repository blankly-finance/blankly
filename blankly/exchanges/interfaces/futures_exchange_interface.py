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
from typing import Union, Optional, List

import numpy
import pandas

from datetime import datetime as dt

from dateutil.parser import parser

import blankly.utils.utils as utils
from blankly.enums import MarginType, HedgeMode, PositionMode, OrderType, Side, TimeInForce, ContractType
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.orders.futures.futures_order import FuturesOrder


class FuturesExchangeInterface(ABCBaseExchangeInterface, abc.ABC):
    exchange_name: str

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

    @staticmethod
    @abc.abstractmethod
    def to_blankly_symbol(symbol: str):
        pass

    @staticmethod
    @abc.abstractmethod
    def to_exchange_symbol(symbol: str):
        pass

    def get_exchange_type(self) -> str:
        """Returns the exchange type (ex. 'binance', 'coinbase', 'alpaca')"""
        return self.exchange_name

    @abc.abstractmethod
    def init_exchange(self):
        """Initializes the exchange"""
        pass

    @abc.abstractmethod
    def get_products(self, symbol: str = None) -> dict:
        """Returns a list of all products traded on this exchange"""
        pass

    @abc.abstractmethod
    def get_account(self, symbol: str = None) -> utils.AttributeDict:
        """Returns account information, or information for only one `symbol` if one is given."""
        pass

    # TODO this metohd name might need to change to get_position ?
    @abc.abstractmethod
    def get_positions(self, symbol: str = None) -> Optional[dict]:
        """Returns position information, or information for only one `symbol` if one is given"""
        pass

    @abc.abstractmethod
    def market_order(self,
                     symbol: str,
                     side: Side,
                     size: float,
                     position: PositionMode = None,
                     reduce_only: bool = None) -> FuturesOrder:
        """Places a market order"""
        pass

    @abc.abstractmethod
    def limit_order(self,
                    symbol: str,
                    side: Side,
                    price: float,
                    size: float,
                    position: PositionMode = None,
                    reduce_only: bool = None,
                    time_in_force: TimeInForce = None) -> FuturesOrder:
        """Places a limit order"""
        pass

    @abc.abstractmethod
    def take_profit(self,
                    symbol: str,
                    side: Side,
                    price: float,
                    size: float,
                    position: PositionMode = None) -> FuturesOrder:
        """Place a take-profit order for a position"""
        pass

    @abc.abstractmethod
    def stop_loss(self,
                  symbol: str,
                  side: Side,
                  price: float,
                  size: float,
                  position: PositionMode = None) -> FuturesOrder:
        """Place a stop-loss order for a position"""
        pass

    @abc.abstractmethod
    def set_hedge_mode(self, hedge_mode: HedgeMode):
        pass

    @abc.abstractmethod
    def get_hedge_mode(self):
        pass

    @abc.abstractmethod
    def set_leverage(self, leverage: int, symbol: str = None):
        pass

    @abc.abstractmethod
    def get_leverage(self, symbol: str = None) -> float:
        pass

    @abc.abstractmethod
    def set_margin_type(self, symbol: str, type: MarginType):
        pass

    @abc.abstractmethod
    def get_margin_type(self, symbol: str):
        pass

    @abc.abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> FuturesOrder:
        """Cancels an order"""
        pass

    @abc.abstractmethod
    def get_open_orders(self, symbol: str = None) -> List[FuturesOrder]:
        """Returns all currently open orders, filtered by `symbol` if one is provided."""
        pass

    @abc.abstractmethod
    def get_order(self, symbol: str, order_id: int) -> FuturesOrder:
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
    def positions(self) -> utils.AttributeDict:
        """Position information"""
        return self.get_positions()

    @property
    def orders(self) -> list:
        """All currently open orders"""
        return self.get_open_orders()

    @property
    def cash(self) -> float:
        """The amount of cash in a portfolio. The currency for 'cash' is set in settings.json"""
        using_setting = self.user_preferences['settings'][
            self.exchange_name]['cash']
        return self.get_account(using_setting)['available']

    @abc.abstractmethod
    def get_funding_rate_history(self, symbol: str, epoch_start: int,
                                 epoch_stop: int) -> list:
        """
        Get the funding rate history between `epoch_start` and `epoch_end`.
        Returns a list of {'rate': int, 'time': int}
        """
        pass

    @abc.abstractmethod
    def get_funding_rate_resolution(self) -> int:
        pass
