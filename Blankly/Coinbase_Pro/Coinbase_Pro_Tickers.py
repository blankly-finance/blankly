"""
    Coinbase Pro ticker manager.
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

import Blankly
import _thread
import json
import ssl
import time
import traceback
from Blankly.IExchange_Ticker import IExchangeTicker
import collections

from websocket import create_connection


def create_ticker_connection(id, url):
    ws = create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})
    request = """{
    "type": "subscribe",
    "product_ids": [
        \"""" + id + """\"
    ],
    "channels": [
        {
            "name": "ticker",
            "product_ids": [
                \"""" + id + """\"
            ]
        }
    ]
    }"""
    ws.send(request)
    return ws


class Tickers(IExchangeTicker):
    def __init__(self, currency_id, log=None, WEBSOCKET_URL="wss://ws-feed.pro.coinbase.com"):
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
            self.ws = create_ticker_connection(self.__id, self.URL)
            self.__response = self.ws.recv()
            _thread.start_new_thread(self.read_websocket, ())
        else:
            if self.ws.connected:
                print("Already running...")
                pass
            else:
                # Use recursion to restart, continue appending to time feed and ticker feed
                self.ws = None
                self.start_websocket()

    def read_websocket(self):
        counter = 0
        # TODO port this to "WebSocketApp" found in the websockets documentation
        while self.ws.connected:
            # In case the user closes while its reading from the websocket
            persist_connected = self.ws.connected
            try:
                received_string = self.ws.recv()
                received = json.loads(received_string)
                self.__most_recent_time = Blankly.utils.epoch_from_ISO8601(received["time"])
                # Modify time to use epoch
                received["time"] = self.__most_recent_time
                self.__most_recent_tick = received
                self.__ticker_feed.append(received)
                self.__time_feed.append(self.__most_recent_time)

                if self.__log:
                    if counter % 100 == 0:
                        self.__file.close()
                        self.__file = open(self.__filePath, 'a')
                    line = received["time"] + "," + str(time.time()) + "," + received["price"] + "," + received[
                        "open_24h"] + "," + received["volume_24h"] + "," + received["low_24h"] + "," + received[
                               "high_24h"] + "," + received["volume_30d"] + "," + received["best_bid"] + "," + received[
                               "best_ask"] + "," + received["last_size"] + "\n"
                    self.__file.write(line)

                # Manage price events and fire for each manager attached
                for i in range(len(self.__callbacks)):
                    self.__callbacks[i].price_event(self.__most_recent_tick)


                counter += 1
            except Exception as e:
                if persist_connected:
                    pass
                else:
                    print(traceback.format_exc())
                    print("Error reading ticker websocket for " + self.__id + ": attempting to re-initialize")
                    # Give a delay so this doesn't eat up from the main thread if it takes many tries to initialize
                    time.sleep(2)
                    self.ws.close()
                    self.ws = create_ticker_connection(self.__id, self.URL)
                    # Update response
                    self.__response = self.ws.recv()

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
