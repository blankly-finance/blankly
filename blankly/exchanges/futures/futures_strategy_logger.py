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
from blankly import FuturesStrategy
from blankly.exchanges.interfaces.futures_exchange_interface import FuturesExchangeInterface
from blankly.exchanges.orders.futures.futures_limit_order import FuturesLimitOrder
from blankly.exchanges.orders.futures.futures_market_order import FuturesMarketOrder
from blankly.utils.utils import AttributeDict


# TODO
class FuturesStrategyLogger(FuturesExchangeInterface):
    interface: FuturesExchangeInterface
    strategy: FuturesStrategy

    def __init__(self, interface=None, strategy=None):
        self.interface = interface
        self.strategy = strategy

    def init_exchange(self):
        return self.interface.init_exchange()

    def get_products(self) -> list:
        return self.interface.get_products()

    def get_account(self, symbol: str = None) -> AttributeDict:
        return self.interface.get_account(symbol)

    def market_order(self, symbol: str, side: str, size: float,
                     position: str) -> FuturesMarketOrder:
        return self.interface.market_order(symbol, side, size, position)

    def limit_order(self, symbol: str, side: str, price: float, size: float,
                    position: str) -> FuturesLimitOrder:
        return self.interface.limit_order(symbol, side, price, size, position)

    def cancel_order(self, order_id: str) -> dict:
        return self.interface.cancel_order(order_id)

    def get_open_orders(self, symbol: str = None) -> list:
        return self.interface.get_open_orders(symbol)

    def get_order(self, order_id: str) -> dict:
        return self.interface.get_order(order_id)

    def get_price(self, symbol: str) -> float:
        return self.interface.get_price(symbol)

    @property
    def account(self) -> AttributeDict:
        return self.interface.account

    @property
    def orders(self) -> list:
        return self.interface.orders

    @property
    def cash(self) -> float:
        return self.interface.cash

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        return self.interface.get_product_history(symbol, epoch_start,
                                                  epoch_stop, resolution)
