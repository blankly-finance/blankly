"""
    Base FuturesExchange class.
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
import time

import blankly
from blankly.exchanges.abc_base_exchange import ABCBaseExchange
from blankly.exchanges.auth.utils import write_auth_cache
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface


class FuturesExchange(ABCBaseExchange, abc.ABC):
    exchange_type: str
    portfolio_name: str

    def __init__(self, exchange_type, portfolio_name, preferences_path):
        self.exchange_type = exchange_type  # binance, ftx
        self.portfolio_name = portfolio_name  # my_cool_portfolio
        self.preferences = blankly.utils.load_user_preferences(
            preferences_path)
        self.models = {}

    @property
    @abc.abstractmethod
    def calls(self):
        """Authenticated direct calls object"""
        pass

    @property
    @abc.abstractmethod
    def interface(self) -> FuturesExchangeInterface:
        """This FuturesExchange's Interface"""
        pass

    def initialize(self):
        """
        Initialize the exchange. This should usually be called at the end of subclass constructors.
        This will report the exchange type to blankly.reporter and initialize the cache for this exchange.
        """
        blankly.reporter.export_used_exchange(self.exchange_type)
        write_auth_cache(self.exchange_type, self.portfolio_name, self.calls)

    def get_name(self) -> str:
        return self.portfolio_name

    def get_type(self) -> str:
        return self.exchange_type

    def get_interface(self):
        return self.interface
