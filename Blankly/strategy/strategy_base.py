"""
    Abstraction for creating event driven user strategies
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
import typing

import pandas as pd
import Blankly
from Blankly.exchanges.exchange import Exchange
from Blankly.utils.time_builder import time_interval_to_seconds


class Strategy:
    def __init__(self, exchange: Exchange, currency_pair='BTC-USD'):
        self.exchange = exchange
        self.Ticker_Manager = Blankly.TickerManager(self.exchange.get_type(), currency_pair)
        self.Orderbook_Manager = Blankly.OrderbookManager(self.exchange.get_type(), currency_pair)
        self.currency_pair = currency_pair
        self.Interface = exchange.get_interface()

        # Create a cache for the current interface, and a wrapped paper trade object for user backtesting
        self.__interface_cache = self.Interface
        self.__paper_trade_exchange = Blankly.PaperTrade(self.exchange)

        self.__schedulers = []

    def add_price_event(self, callback: typing.Callable, currency_pair: str, resolution: str):
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
            self.__schedulers.append(
                Blankly.Scheduler(self.__price_event_websocket, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  currency_pair=currency_pair)
            )
        else:
            # Use the API
            self.__schedulers.append(
                Blankly.Scheduler(self.__price_event_rest, resolution,
                                  initially_stopped=True,
                                  callback=callback,
                                  currency_pair=currency_pair)
            )

    def __idle_event(self):
        """
        Function to skip & ignore callbacks
        """
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

    def add_orderbook_event(self, callback: typing.Callable, currency_pair: str):
        """
        Add Orderbook Event
        Args:
            callback: The price event callback that will be added to the current ticker and run at the proper resolution
            currency_pair: Currency pair to create the orderbook for
        """
        # since it's less than 10 sec, we will just use the websocket feed - exchanges don't like fast calls
        self.Orderbook_Manager.create_orderbook(self.__idle_event, currency_id=currency_pair)

        # TODO the tickers need some type of argument passing & saving like scheduler so that the 1 second min isn't
        #  required
        self.__schedulers.append(
            Blankly.Scheduler(self.__orderbook_event_websocket, 1,
                              initially_stopped=True,
                              callback=callback, currency_pair=currency_pair)
        )

    def start(self):
        for i in self.__schedulers:
            i.start()

    def __orderbook_event_websocket(self, **kwargs):
        callback = kwargs['callback']
        currency_pair = kwargs['currency_pair']

        price = self.Orderbook_Manager.get_most_recent_tick(override_currency=currency_pair)
        callback(price, currency_pair)

    def backtest(self, asset_id: str, price_data: pd.DataFrame):
        """
        Turn this strategy into a backtest.
        Make sure the price events use a paper trade object unless you want actual live trading

        Args:
            asset_id (str): Asset ID of the price passed in - such as "BTC-USD"
            price_data (dataframe): Price dataframe from blankly historical download
        """
        self.Interface = self.__paper_trade_exchange.get_interface()

        # Append each of the events the class defines into the backtest
        for i in self.__schedulers:
            kwargs = i.get_kwargs()
            self.__paper_trade_exchange.append_backtest_price_event(callback=kwargs['callback'],
                                                                    asset_id=kwargs['currency_pair'],
                                                                    time_interval=i.get_interval()
                                                                    )

        # Append the price data just passed in
        self.__paper_trade_exchange.append_backtest_price_data(asset_id, price_data)

        # Run the backtest & return results
        results = self.__paper_trade_exchange.backtest()

        # Clean up
        self.Interface = self.__interface_cache

        return results

