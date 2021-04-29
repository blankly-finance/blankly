"""
    Abstraction for websocket manager objects
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
import Blankly.utils.utils
from Blankly.exchanges.IExchange_Websocket import IExchangeWebsocket


class WebsocketManager(IExchangeWebsocket):
    def __init__(self, websockets, default_currency, default_exchange):
        self.__websockets = websockets
        self.__default_currency = default_currency
        self.__default_exchange = default_exchange

    def close_all_websockets(self):
        """
        Iterate through orderbooks and make sure they're closed
        """
        self.__recursive_close(self.__websockets)

    def __recursive_close(self, d):
        for k, v in d.items():
            if isinstance(v, dict):
                self.__recursive_close(v)
            else:
                d[k].close_websocket()

    def __evaluate_overrides(self, override_currency, override_exchange):
        """
        Switches to inputted exchanges, used in the public methods
        """
        # Issues could arise if the user specifies a different exchange but not a different currency. It would run
        # that default on the new exchange. Not great behavior unless they're clever
        if override_currency is not None:
            currency_id = override_currency
        else:
            currency_id = self.__default_currency
        if override_exchange is not None:
            exchange = override_exchange
        else:
            exchange = self.__default_exchange

        if exchange == "binance":
            currency_id = Blankly.utils.to_exchange_coin_id(currency_id, "binance")
        return currency_id, exchange

    def get_ticker(self, currency_id, override_exchange=None):
        """
        Retrieve the ticker attached to a currency
        Args:
            currency_id: The currency ID of ticker (required) such as "BTC-USD"
            override_exchange: Override the default to get tickers for different exchanges
        """
        if override_exchange is None:
            return self.__websockets[self.__default_exchange][currency_id]
        else:
            return self.__websockets[override_exchange][currency_id]

    def get_all_tickers(self):
        """
        Get the tickers object dictionary. This can be used for individual management, or to stop using the manager.
        Returns:
            Dictionary with tickers referenced for each currency
        """
        return self.__websockets

    """
    Ticker functions/overridden
    """
    def append_callback(self, callback_object, override_currency=None, override_exchange=None):
        """
        This bypasses all processing that a manager class may do before returning to the user's main.
        For example with an orderbook feed, this will return the ticks instead of a sorted orderbook
        This can be very useful in working with multiple tickers, but not necessary on a simple bot.

        Args:
            callback_object: Reference for the callback function. The price_event(self, tick)
                function would be passed in as just self.price_event  -- no parenthesis or arguments, just the object
            override_currency: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        self.__websockets[exchange][currency_id].append_callback(callback_object)

    def is_websocket_open(self, override_currency=None, override_exchange=None):
        """
        Check if the websocket attached to a currency is open
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        return self.__websockets[exchange][currency_id].is_websocket_open()

    def get_most_recent_time(self, override_currency=None, override_exchange=None):
        """
        Get the most recent time associated with the most recent tick
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        return self.__websockets[exchange][currency_id].get_most_recent_time()

    def get_time_feed(self, override_currency=None, override_exchange=None):
        """
        Get a time array associated with the ticker feed.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        return self.__websockets[exchange][currency_id].get_time_feed()

    def get_feed(self, override_currency=None, override_exchange=None):
        """
        Get the full ticker array. This can be extremely large.
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        return self.__websockets[exchange][currency_id].get_feed()

    def get_response(self, override_currency=None, override_exchange=None):
        """
        Get the exchange's response to the request to subscribe to a feed
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        return self.__websockets[exchange][currency_id].get_response()

    def close_websocket(self, override_currency=None, override_exchange=None):
        """
        Close a websocket thread
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        self.__websockets[exchange][currency_id].close_websocket()

    def restart_ticker(self, override_currency=None, override_exchange=None):
        """
        Restart a websocket feed after asking it to stop
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)

        self.__websockets[exchange][currency_id].restart_ticker()

    def get_most_recent_tick(self, override_currency=None, override_exchange=None):
        """
        Get the most recent tick received
        """
        currency_id, exchange = self.__evaluate_overrides(override_currency, override_exchange)
        # if self.__default_exchange == "coinbase_pro":
        # TODO fix the returned value below, really this needs a class like in Binance that can create a callback to
        #  allow a pointer to be subbed in for whichever exchange/currency/websocket type is overridden
        # to allow
        return self.__websockets[exchange][currency_id].get_most_recent_tick()
