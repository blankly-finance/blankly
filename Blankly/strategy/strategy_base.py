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
        resolution = time_interval_to_seconds(resolution)
        if resolution < 10:
            # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
            self.Ticker_Manager.create_ticker(self.__idle_event, currency_id=currency_pair)
            Blankly.Scheduler(self.__price_event_websocket, resolution, callback=callback, currency_pair=currency_pair)
        else:
            # use the API 
            Blankly.Scheduler(self.__price_event_rest, resolution, callback=callback, currency_pair=currency_pair)

    def __idle_event(self):
        pass

    def __price_event_rest(self, **kwargs):
        callback = kwargs['callback']
        currency_pair = kwargs['currency_pair']

        price = self.Interface.get_price(currency_pair)
        callback(price, currency_pair)

    def __price_event_websocket(self, **kwargs):
        callback = kwargs['callback']
        currency_pair = kwargs['currency_pair']

        price = self.Ticker_Manager.get_most_recent_tick(override_currency=currency_pair)
        callback(price, currency_pair)

    def add_orderbook_event(self, callback, currency_pair):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            currency_pair: Currency pair to create the orderbook for
        """
        # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
        self.Ticker_Manager.create_ticker(self.__idle_event, currency_id=currency_pair)

        # TODO the tickers need some type of argument passing & saving like scheduler so that the 1 second min isn't
        #  required
        Blankly.Scheduler(self.__orderbook_event_websocket, 1, callback=callback, currency_pair=currency_pair)

    def __orderbook_event_websocket(self, **kwargs):
        callback = kwargs['callback']
        currency_pair = kwargs['currency_pair']

        price = self.Orderbook_Manager.get_most_recent_tick(override_currency=currency_pair)
        callback(price, currency_pair)

