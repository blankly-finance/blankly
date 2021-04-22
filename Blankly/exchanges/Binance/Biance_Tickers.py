"""
    Binance ticker class.
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

import websocket
import time
from Blankly.exchanges.IExchange_Ticker import IExchangeTicker
import collections
import json
import traceback
import Blankly
import threading

try:
    import thread
except ImportError:
    import _thread as thread


class Tickers(IExchangeTicker):
    def __init__(self, currency_id, log=None, WEBSOCKET_URL="wss://stream.binance.com:9443/ws"):
        """
        Create and initialize the ticker
        Args:
            currency_id: Currency to initialize on such as "BTC-USD"
            log: Fill this with a path to a log file that should be created
            WEBSOCKET_URL: Default websocket URL feed.
        """
        self.__id = currency_id

        # Initialize log file
        if log is not None:
            self.__log = True
            self.__filePath = log
            try:
                self.__file = open(log, 'xa')
                self.__file.write(
                    "time,system_time,price,open_24h,volume_24h,low_24h,high_24h,volume_30d,best_bid,best_ask,"
                    "last_size\n")
            except FileExistsError:
                self.__file = open(log, 'a')
        else:
            self.__log = False

        self.URL = WEBSOCKET_URL
        self.ws = None
        self.__response = None
        self.__most_recent_tick = None
        self.__most_recent_time = None
        self.__callbacks = []

        # Reload preferences
        self.__preferences = Blankly.utils.load_user_preferences()
        self.__ticker_feed = collections.deque(maxlen=self.__preferences["settings"]["ticker_buffer_size"])
        self.__time_feed = collections.deque(maxlen=self.__preferences["settings"]["ticker_buffer_size"])

        # Start the websocket
        self.start_websocket()

    def start_websocket(self):
        """
        Restart websocket if it was asked to stop.
        """
        if self.ws is None:
            websocket.enableTrace(True)
            self.ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
            thread = threading.Thread(target=self.read_websocket)
            thread.start()
        else:
            if self.ws.connected:
                print("Already running...")
                pass
            else:
                # Use recursion to restart, continue appending to time feed and ticker feed
                self.ws = None
                self.start_websocket()


    def read_websocket(self):
        self.ws.run_forever()

    def on_message(self, ws, message):
        print(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        request = """ {
            "method": "SUBSCRIBE",
            "params": [
                "btcusdt@depth@100ms"
            ],
            "id": 1
        }
        """
        ws.send(request)

    """ Required in manager """
    def is_websocket_open(self):
        return self.ws.connected

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
    def get_ticker_feed(self):
        return list(self.__ticker_feed)

    """ Required in manager """
    def get_response(self):
        return self.__response

    """ Required in manager """
    def close_websocket(self):
        if self.ws.connected:
            self.ws.close()
        else:
            print("Websocket for " + self.__id + " is already closed")

    """ Required in manager """
    def restart_ticker(self):
        self.start_websocket()

