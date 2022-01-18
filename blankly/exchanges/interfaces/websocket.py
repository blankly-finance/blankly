"""
    Core logic to reduce duplication across websocket implementations
    Copyright (C) 2022  Emerson Dove

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
import collections
import threading

import websocket

import blankly.utils.utils
from blankly.exchanges.abc_exchange_websocket import ABCExchangeWebsocket
from blankly.utils.utils import info_print


class Websocket(ABCExchangeWebsocket, abc.ABC):
    def __init__(self, symbol, stream, log, log_message, url, pre_event_callback):
        self.symbol = symbol
        self.stream = stream

        # Initialize log file
        if log is not None:
            self.log = True
            self.file_path = log
            try:
                self.__file = open(log, 'x+')
                self.__file.write(log_message)
            except FileExistsError:
                self.__file = open(log, 'a')
        else:
            self.log = False

        self.url = url

        self.thread = None
        self.message_count = 0

        self.response = None
        self.most_recent_tick = None
        self.most_recent_time = None
        self.callbacks = []
        self.pre_event_callback = pre_event_callback

        # Reload preferences
        self.preferences = blankly.utils.load_user_preferences()
        buffer_size = self.preferences['settings']['websocket_buffer_size']
        self.ticker_feed = collections.deque(maxlen=buffer_size)
        self.time_feed = collections.deque(maxlen=buffer_size)

        self.ws = None

    def start_websocket(self, on_open: callable, on_message: callable, on_error: callable, on_close: callable,
                        target: callable):
        """
        Restart websocket if it was asked to stop.
        """
        if self.ws is None:
            self.ws = websocket.WebSocketApp(self.url,
                                             on_open=on_open,
                                             on_message=on_message,
                                             on_error=on_error,
                                             on_close=on_close)
            self.thread = threading.Thread(target=target)
            self.thread.start()
        else:
            if self.thread.is_alive():
                info_print("Already running...")
            else:
                # Use recursion to restart, continue appending to time feed and ticker feed
                self.ws = None
                self.start_websocket(on_open, on_message, on_error, on_close, target)

    def log_response(self, logging_callback: callable, message: dict):
        # Run callbacks on message
        if self.log:
            if self.message_count % 100 == 0:
                self.__file.close()
                self.__file = open(self.file_path, 'a')
            line = logging_callback(message)
            self.__file.write(line)
    """
    The are access functions
    """
    """ Required in manager """

    def is_websocket_open(self):
        if self.thread is not None:
            return self.thread.is_alive()
        else:
            return False

    def get_currency_id(self):
        return self.symbol

    """ Required in manager """

    def append_callback(self, obj):
        self.callbacks.append(obj)

    """ Define a variable each time so there is no array manipulation """
    """ Required in manager """

    def get_most_recent_tick(self):
        return self.most_recent_tick

    """ Required in manager """

    def get_most_recent_time(self):
        return self.most_recent_time

    """ Required in manager """

    def get_time_feed(self):
        return list(self.time_feed)

    """ Parallel with time feed """
    """ Required in manager """

    def get_feed(self):
        return list(self.ticker_feed)

    """ Required in manager """

    def get_response(self):
        return self.response

    """ Required in manager """

    def close_websocket(self):
        if self.thread is not None and self.thread.is_alive():
            self.ws.close()
        else:
            print("Websocket for " + self.symbol + '@' + self.stream + " is already closed")

    @abc.abstractmethod
    def on_open(self, ws):
        pass

    @abc.abstractmethod
    def on_error(self, ws, error):
        pass

    @abc.abstractmethod
    def on_message(self, ws, message):
        pass

    @abc.abstractmethod
    def on_close(self, ws):
        pass
