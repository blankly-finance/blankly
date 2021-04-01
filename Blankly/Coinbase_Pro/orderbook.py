"""
    Coinbase Pro orderbook websocket feed.
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

import _thread
import json
import ssl
import time
import traceback

from websocket import create_connection


def create_websocket_connection(id, url):
    ws = create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})
    request = """{
    "type": "subscribe",
    "product_ids": [
        \"""" + id + """\"
    ],
    "channels": [
        "full"
    ]
    }"""
    ws.send(request)
    return ws


class OrderBook:
    def __init__(self, currency_id, WEBSOCKET_URL="wss://ws-feed.pro.coinbase.com"):
        """
        Create and initialize the orderbook connection
        Args:
            currency_id: Currency to listen on such as "BTC-USD"
            WEBSOCKET_URL: Default websocket URL feed.
        """
        self.__id = currency_id

        self.URL = WEBSOCKET_URL
        self.ws = None
        self.__response = None
        self.__orderbook_feed = []
        self.__timeFeed = []
        self.__mostRecentTick = None
        self.__callbacks = []
        # Start the websocket
        self.start_websocket()

    # This could be made static with some changes, would make the code in the loop cleaner
    def start_websocket(self):
        """
        Restart websocket if it was asked to stop.
        """
        if self.ws is None:
            self.ws = create_websocket_connection(self.__id, self.URL)
            self.__response = self.ws.recv()
            _thread.start_new_thread(self.read_websocket, ())
        else:
            if self.ws.connected:
                print("Already running...")
                pass
            else:
                # Use recursion to restart, continue appending to time feed and orderbook feed
                self.ws = None
                self.start_websocket()

    def read_websocket(self):
        # TODO port this to "WebSocketApp" found in the websockets documentation
        while self.ws.connected:
            # In case the user closes while its reading from the websocket
            persist_connected = self.ws.connected
            try:
                received_string = self.ws.recv()
                received = json.loads(received_string)
                # self.__orderbook_feed.append(received)
                # self.__mostRecentTick = received

                # Manage price events and fire for each manager attached
                for i in range(len(self.__callbacks)):
                    self.__callbacks[i].orderbook_event(received)

                # self.__timeFeed.append(Blankly.utils.epoch_from_ISO8601(received["time"]))
            except Exception as e:
                if persist_connected:
                    pass
                else:
                    print(traceback.format_exc())
                    print("Error reading orderbook for " + self.__id + ": attempting to re-initialize")
                    # Give a delay so this doesn't eat up from the main thread if it takes many tries to initialize
                    time.sleep(2)
                    self.ws.close()
                    self.ws = create_websocket_connection(self.__id, self.URL)
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
        return self.__mostRecentTick

    """ Required in manager """
    def get_most_recent_time(self):
        return self.__timeFeed[-1]

    """ Required in manager """
    def get_time_feed(self):
        return self.__timeFeed

    """ Parallel with time feed """
    """ Required in manager """
    def get_orderbook_feed(self):
        return self.__orderbook_feed

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
    def restart_websocket(self):
        self.start_websocket()
