"""
    User abstraction for Blankly Bot
    Copyright (C) 2021  Emerson Dove, Brandon Fan

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


import Blankly
from Blankly.strategy.order import Order
from Blankly.utils.time_builder import time_interval_to_seconds


class Strategy:
    def __init__(self, exchange, currency_pair='BTC-USD'):
        self.exchange = exchange
        self.price_funcs = []
        self.order_funcs = []
        self.Ticker_Manager = Blankly.TickerManager(self.exchange.get_type(), currency_pair)
        self.Orderbook_Manager = Blankly.OrderbookManager(self.exchange.get_type(), currency_pair)
        self.currency_pair = currency_pair
        self.Interface = exchange.get_interface()

    def add_price_event(self, callback, currency_pair, resolution):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            currency_pair: Currency pair to create the price event for
            resolution: The resolution that the callback will be run - in seconds
        """
        if time_interval_to_seconds(resolution) < 60:
            # since it's less than 60, we will just use the websocket feed
            self.Ticker_Manager.append_callback(self.__price_event_websocket(callback))
        else:
            # use the API 
            Blankly.Scheduler(self.__price_event_rest, resolution, callback=callback)

    def add_orderbook_event(self, callback):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
        """
        self.Orderbook_Manager.append_callback(self.__orderbook_event)

    def __price_event_rest(self, **kwargs):
        callback = kwargs['callback']
        price = self.Interface.get_price(self.currency_pair)
        order = callback(price, self.currency_pair)
        if order is not None:
            if not isinstance(order, Order):
                raise TypeError("Expected an order type of Order when order is not none but got {}".format(type(order)))
            else:
                if order.type == 'limit':
                    return self.Interface.limit_order(self.currency_pair, order.side, order.price, order.size)
                return self.Interface.market_order(self.currency_pair, order.side, order.price, order.size)
        return

    def __price_event_websocket(self, callback):
        price = self.Ticker_Manager.get_most_recent_tick()
        callback(price, self.currency_pair)
        return

    def __orderbook_event(self, callback):
        orderbook = self.Ticker_Manager.get_most_recent_tick()
        order = callback(orderbook, self.currency_pair)
        if order is not None:
            if not isinstance(order, Order):
                raise TypeError("Expected an order type of Order when order is not none but got {}".format(type(order)))
            else:
                if order.type == 'limit':
                    return self.Interface.limit_order(self.currency_pair, order.side, order.price, order.size)
                return self.Interface.market_order(self.currency_pair, order.side, order.price, order.size)
        return
