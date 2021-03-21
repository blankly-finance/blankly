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

import _thread, json, time, Blankly.Utils, ssl
from websocket import create_connection

# TODO add an inherited object so that each of these have a similar way of interacting
class Tickers:
    def __init__(self, currency_id, log="", show=False, WEBSOCKET_URL="wss://ws-feed.pro.coinbase.com"):
        self.__id = currency_id
        if (len(log) > 1):
            self.__log = True
            self.__filePath = log
            try:
                self.__file = open(log, 'xa')
                self.__file.write(
                    "time,system_time,price,open_24h,volume_24h,low_24h,high_24h,volume_30d,best_bid,best_ask,"
                    "last_size\n")
            except:
                self.__file = open(log, 'a')
        else:
            self.__log = False

        self.__webSocketClosed = False
        ws = self.create_ticker_connection(currency_id, WEBSOCKET_URL)
        self.__response = ws.recv()
        self.__show = show
        _thread.start_new_thread(self.read_websocket, (ws,))
        self.__tickerFeed = []
        self.__timeFeed = []
        self.__websocket = ws
        self.__mostRecentTick = None
        self.__managers = []

    def create_ticker_connection(self, id, url):
        # ws = create_connection(url)
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

    def close_websocket(self):
        self.__webSocketClosed = True
        print("Closed websocket for " + self.__id)

    def read_websocket(self, ws):
        counter = 0
        try:
            while not self.__webSocketClosed:
                receivedString = ws.recv()
                received = json.loads(receivedString)
                if self.__show:
                    print(received)
                if self.__log:
                    if (counter % 100 == 0):
                        self.__file.close()
                        self.__file = open(self.__filePath, 'a')
                    line = received["time"] + "," + str(time.time()) + "," + received["price"] + "," + received[
                        "open_24h"] + "," + received["volume_24h"] + "," + received["low_24h"] + "," + received[
                               "high_24h"] + "," + received["volume_30d"] + "," + received["best_bid"] + "," + received[
                               "best_ask"] + "," + received["last_size"] + "\n"
                    self.__file.write(line)
                    print(receivedString)
                self.__tickerFeed.append(received)
                self.__mostRecentTick = received

                # Manage price events and fire for each manager attached
                for i in range(len(self.__managers)):
                    self.__managers[i].price_event(self.__mostRecentTick)

                self.__timeFeed.append(Blankly.Utils.epoch_from_ISO8601(received["time"]))
                counter += 1
        except Exception as e:
            print("Error reading websocket")
        ws.close()
        print("websocket closed")

    def is_websocket_open(self):
        return not self.__webSocketClosed

    """ Parallel with time feed """

    def get_ticker_feed(self):
        return self.__tickerFeed

    def get_time_feed(self):
        return self.__timeFeed

    """ Define a variable each time so there is no array manipulation """

    def get_most_recent_tick(self):
        return self.__mostRecentTick

    def get_most_recent_time(self):
        return self.__timeFeed[-1]

    def get_response(self):
        return self.__response

    def update_show(self, value):
        self.__show = value

    def append_callback(self, obj):
        self.__managers.append(obj)

    def get_currency_id(self):
        return self.__id
