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
import blankly.utils.utils
from blankly.exchanges.abc_exchange_websocket import ABCExchangeWebsocket


class WebsocketManager(ABCExchangeWebsocket):
    def __init__(self, websockets, default_symbol, default_exchange):
        self.websockets = websockets
        self.__default_symbol = default_symbol
        self.__default_exchange = default_exchange

        self.preferences = blankly.utils.load_user_preferences()

    def close_all_websockets(self):
        """
        Iterate through orderbooks and make sure they're closed
        """
        self.__recursive_close(self.websockets)

    def __recursive_close(self, d):
        for k, v in d.items():
            if isinstance(v, dict):
                self.__recursive_close(v)
            else:
                d[k].close_websocket()

    def __evaluate_overrides(self, override_symbol, override_exchange):
        """
        Switches to inputted exchanges, used in the public methods
        """
        # Issues could arise if the user specifies a different exchange but not a different currency. It would run
        # that default on the new exchange. Not great behavior unless they're clever
        if override_symbol is not None:
            currency_id = override_symbol
        else:
            currency_id = self.__default_symbol
        if override_exchange is not None:
            exchange = override_exchange
        else:
            exchange = self.__default_exchange

        if exchange == "binance":
            currency_id = blankly.utils.to_exchange_symbol(currency_id, "binance")
        return self.websockets[exchange][currency_id]

    def get_ticker(self, symbol, override_exchange=None):
        """
        Retrieve the ticker attached to a currency
        Args:
            symbol: The currency ID of ticker (required) such as "BTC-USD"
            override_exchange: Override the default to get tickers for different exchanges
        """
        if override_exchange is None:
            return self.websockets[self.__default_exchange][symbol]
        else:
            return self.websockets[override_exchange][symbol]

    def get_all_tickers(self) -> dict:
        """
        Get the tickers object dictionary. This can be used for individual management, or to stop using the manager.
        Returns:
            Dictionary with tickers referenced for each currency
        """
        return self.websockets

    """
    Ticker functions/overridden
    """

    def append_callback(self, callback_object, override_symbol=None, override_exchange=None):
        """
        This bypasses all processing that a manager class may do before returning to the user's main.
        For example with an orderbook feed, this will return the ticks instead of a sorted orderbook
        This can be very useful in working with multiple tickers, but not necessary on a simple bot.

        Args:
            callback_object: Reference for the callback function. The price_event(self, tick)
                function would be passed in as just self.price_event  -- no parenthesis or arguments, just the object
            override_symbol: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        websocket.append_callback(callback_object)

    def is_websocket_open(self, override_symbol=None, override_exchange=None) -> bool:
        """
        Check if the websocket attached to a currency is open
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        return websocket.is_websocket_open()

    def get_most_recent_time(self, override_symbol=None, override_exchange=None):
        """
        Get the most recent time associated with the most recent tick
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        return websocket.get_most_recent_time()

    def get_time_feed(self, override_symbol=None, override_exchange=None):
        """
        Get a time array associated with the ticker feed.
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        return websocket.get_time_feed()

    def get_feed(self, override_symbol=None, override_exchange=None):
        """
        Get the full ticker array. This can be extremely large.
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        return websocket.get_feed()

    def get_response(self, override_symbol=None, override_exchange=None):
        """
        Get the exchange's response to the request to subscribe to a feed
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        return websocket.get_response()

    def close_websocket(self, override_symbol=None, override_exchange=None):
        """
        Close a websocket thread
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        websocket.close_websocket()

    def restart_ticker(self, override_symbol=None, override_exchange=None):
        """
        Restart a websocket feed after asking it to stop
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)

        websocket.restart_ticker()

    def get_most_recent_tick(self, override_symbol=None, override_exchange=None):
        """
        Get the most recent tick received
        """
        websocket = self.__evaluate_overrides(override_symbol, override_exchange)
        # TODO fix the returned value below, really this needs a class like in binance that can create a callback to
        #  allow a pointer to be subbed in for whichever exchange/currency/websocket type is overridden
        return websocket.get_most_recent_tick()
