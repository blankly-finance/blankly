"""
    binance ticker class.
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

import collections
import json
import threading
import traceback

import websocket

import blankly
import blankly.exchanges.interfaces.binance.binance_websocket_utils as websocket_utils
from blankly.exchanges.abc_exchange_websocket import ABCExchangeWebsocket
from blankly.utils.utils import info_print


class Tickers(ABCExchangeWebsocket):
    def __init__(self, symbol, stream, log=None, initially_stopped=False,
                 WEBSOCKET_URL="wss://stream.binance.{}:9443/ws"):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "btcusdt"
            stream: Stream to use, such as "depth" or "trade"
            log: Fill this with a path to a log file that should be created
            WEBSOCKET_URL: Default websocket URL feed.
        """
        self.__id = symbol
        self.__stream = stream
        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)

        # Initialize log file
        if log is not None:
            self.__log = True
            self.__filePath = log
            try:
                self.__file = open(log, 'x+')
                self.__file.write(log_message)
            except FileExistsError:
                self.__file = open(log, 'a')
        else:
            self.__log = False

        # Reload preferences
        self.__preferences = blankly.utils.load_user_preferences()

        # Add the TLD into the URL if necessary
        self.URL = WEBSOCKET_URL.format(self.__preferences['settings']['binance']['binance_tld'])
        self.ws = None
        self.__response = None
        self.__most_recent_tick = None
        self.__most_recent_time = None
        # Create the thread object here
        self.__thread = threading.Thread(target=self.read_websocket)
        self.__callbacks = []
        # This is created so that we know when a message has come back that we're waiting for
        self.__message_count = 0

        buffer_size = self.__preferences["settings"]["websocket_buffer_size"]
        self.__ticker_feed = collections.deque(maxlen=buffer_size)
        self.__time_feed = collections.deque(maxlen=buffer_size)

        # Start the websocket
        if not initially_stopped:
            self.start_websocket()

    def start_websocket(self):
        """
        Restart websocket if it was asked to stop.
        """
        if self.ws is None:
            self.ws = websocket.WebSocketApp(self.URL,
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
            self.__thread = threading.Thread(target=self.read_websocket)
            self.__thread.start()
        else:
            if self.__thread.is_alive():
                info_print("Already running...")
            else:
                # Use recursion to restart, continue appending to time feed and ticker feed
                self.ws = None
                self.start_websocket()

    def read_websocket(self):
        # Main thread to sit here and run
        self.ws.run_forever()
        # This repeats the close behavior just in case something happens

    def on_message(self, ws, message):
        self.__message_count += 1
        message = json.loads(message)
        try:
            self.__most_recent_time = message['E']
            self.__time_feed.append(self.__most_recent_time)

            # Run callbacks on message
            if self.__log:
                if self.__message_count % 100 == 0:
                    self.__file.close()
                    self.__file = open(self.__filePath, 'a')
                line = self.__logging_callback(message)
                self.__file.write(line)

            interface_message = self.__interface_callback(message)
            self.__ticker_feed.append(interface_message)
            self.__most_recent_tick = interface_message
            for i in self.__callbacks:
                i(interface_message)
        except KeyError:
            # If the try below figures this out then we don't have to traceback
            error_found = False
            try:
                if message['result'] is None:
                    self.__response = message
                    error_found = True
            except KeyError:
                traceback.print_exc()

            if not error_found:
                traceback.print_exc()

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        # This repeats the close behavior just in case something happens
        pass

    def on_open(self, ws):
        request = '{"method": ' \
                  '"SUBSCRIBE","params": ' \
                  '["' + self.__id + '@' + self.__stream + \
                  '"],"id": 1}'
        ws.send(request)

    """ Required in manager """

    def is_websocket_open(self):
        return self.__thread.is_alive()

    def get_currency_id(self):
        return self.__id

    """ Required in manager """

    def append_callback(self, obj):
        self.__callbacks.append(obj)

    """ Define a variable each time so there is no array manipulation """
    """ Required in manager """

    def get_most_recent_tick(self):
        return self.__most_recent_tick

    """ Required in manager """

    def get_most_recent_time(self):
        return self.__most_recent_time

    """ Required in manager """

    def get_time_feed(self):
        return list(self.__time_feed)

    """ Parallel with time feed """
    """ Required in manager """

    def get_feed(self):
        return list(self.__ticker_feed)

    """ Required in manager """

    def get_response(self):
        return self.__response

    """ Required in manager """

    def close_websocket(self):
        if self.__thread.is_alive():
            self.ws.close()
        else:
            print("Websocket for " + self.__id + '@' + self.__stream + " is already closed")

    """ Required in manager """

    def restart_ticker(self):
        self.start_websocket()
