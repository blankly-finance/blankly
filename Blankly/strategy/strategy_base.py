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

        self.Schedulers = []

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
            self.Schedulers.append(
                Blankly.Scheduler(self.__price_event_websocket, resolution,
                                  callback=callback, currency_pair=currency_pair)
            )
        else:
            # use the API
            self.Schedulers.append(
                Blankly.Scheduler(self.__price_event_rest, resolution, callback=callback, currency_pair=currency_pair)
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
        self.Schedulers.append(
            Blankly.Scheduler(self.__orderbook_event_websocket, 1, callback=callback, currency_pair=currency_pair)
        )

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

        # Ensure that the current exchange is a backtesting exchange
        backtesting_exchange = self.exchange
        if not self.exchange.get_type() == "paper_trade":
            backtesting_exchange = Blankly.PaperTrade(backtesting_exchange)

        # Append each of the events the class defines into the backtest
        for i in self.Schedulers:
            i = i  # type: Blankly.Scheduler
            kwargs = i.get_kwargs()
            backtesting_exchange.append_backtest_price_event(callback=i.get_callback(),
                                                             asset_id=kwargs['currency_pair'],
                                                             time_interval=i.get_interval()
                                                             )

        # Append the price data just passed in
        backtesting_exchange.append_backtest_price_data(asset_id, price_data)

        # Run the backtest & return results
        return backtesting_exchange.backtest()
