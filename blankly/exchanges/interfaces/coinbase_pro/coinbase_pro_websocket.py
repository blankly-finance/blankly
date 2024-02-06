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

import json
import time
import traceback

import blankly
import blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
from blankly.utils.utils import info_print


def create_ticker_connection(id, url, channel):
    ws = None  # create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})
    request = """{
    "type": "subscribe",
    "product_ids": [
        \"""" + id + """\"
    ],
    "channels": [ \"""" + channel + """\" ]
    }"""
    ws.send(request)
    return ws


# This could be needed:
# "channels": [
#     {
#         "name": "ticker",
#         "product_ids": [
#             \"""" + id + """\"
#         ]
#     }
# ]


class Tickers(Websocket):
    def __init__(self, symbol, stream, log=None,
                 pre_event_callback=None, initially_stopped=False, websocket_url="wss://ws-feed.pro.coinbase.com",
                 **kwargs):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "BTC-USD"
            log: Fill this with a path to a log file that should be created
            websocket_url: Default websocket URL feed.
        """
        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)

        super().__init__(symbol, stream, log, log_message, websocket_url, pre_event_callback, kwargs)

        self.__pre_event_callback_filled = False

        # Start the websocket
        if not initially_stopped:
            self.start_websocket(
                self.on_open,
                self.on_message,
                self.on_error,
                self.on_close,
                self.run_forever
            )

    def run_forever(self):
        """
        This is the target from the super

        It's renamed to run_forever in coinbase pro because I think that ancient code below is cool
        """
        self.ws.run_forever()

    """
    This function has some of the oldest code in the entire package
    """
    def read_websocket(self):
        # This is unique because coinbase first sends the entire orderbook to use
        if self.__pre_event_callback is not None and self.__stream == "level2":
            received_string = json.loads(self.ws.recv())
            if received_string['type'] == 'snapshot':
                try:
                    self.__pre_event_callback(received_string)
                except Exception:
                    traceback.print_exc()

        counter = 0
        # TODO port this to "WebSocketApp" found in the websockets documentation
        while self.ws.connected:
            # In case the user closes while its reading from the websocket, this will let it expire
            persist_connected = self.ws.connected
            try:
                received_string = self.ws.recv()
                received = json.loads(received_string)
                # Modify time to use epoch
                self.__most_recent_time = blankly.utils.epoch_from_iso8601(received["time"])
                received["time"] = self.__most_recent_time
                self.__time_feed.append(self.__most_recent_time)

                if self.__log:
                    if counter % 100 == 0:
                        self.__file.close()
                        self.__file = open(self.__filePath, 'a')
                    line = self.__logging_callback(received)
                    self.__file.write(line)

                # Manage price events and fire for each manager attached
                interface_message = self.__interface_callback(received)
                self.__ticker_feed.append(interface_message)
                self.__most_recent_tick = interface_message

                try:
                    for i in self.__callbacks:
                        i(interface_message)
                except Exception:
                    traceback.print_exc()

                counter += 1
            except Exception as e:
                if persist_connected:
                    traceback.print_exc()
                    pass
                else:
                    traceback.print_exc()
                    print("Error reading ticker websocket for " + self.__id + " on " +
                          self.__stream + ": attempting to re-initialize")
                    # Give a delay so this doesn't eat up from the main thread if it takes many tries to initialize
                    time.sleep(2)
                    self.ws.close()
                    # Update response
                    self.response = self.ws.recv()

    def on_message(self, ws, message):
        received_string = message
        received = json.loads(received_string)

        if received['type'] == 'subscriptions':
            info_print(f"Subscribed to {received['channels']}")
            return

        # This is unique because coinbase first sends the entire orderbook to use
        if (self.pre_event_callback is not None) and (not self.__pre_event_callback_filled) and \
                (self.stream == "level2"):
            if received['type'] == 'snapshot':
                try:
                    self.pre_event_callback(received)
                except Exception:
                    traceback.print_exc()

            self.__pre_event_callback_filled = True
            return

        # Modify time to use epoch
        self.most_recent_time = blankly.utils.epoch_from_iso8601(received["time"])
        received["time"] = self.most_recent_time
        self.time_feed.append(self.most_recent_time)

        self.log_response(self.__logging_callback, received)

        # Manage price events and fire for each manager attached
        interface_message = self.__interface_callback(received)
        self.ticker_feed.append(interface_message)
        self.most_recent_tick = interface_message

        try:
            for i in self.callbacks:
                i(interface_message, **self.kwargs)
        except Exception:
            traceback.print_exc()

        self.message_count += 1

    def on_error(self, ws, error):
        info_print(error)

    def on_close(self, ws):
        # This repeats the close behavior just in case something happens
        pass

    def on_open(self, ws):
        request = json.dumps({
            'type': 'subscribe',
            'product_ids': [self.symbol],
            'channels': [self.stream]
        })
        ws.send(request)

    def restart_ticker(self):
        """
        This is the only abstract function that should be placed individually
        into each websocket file
        """
        self.start_websocket(
            self.on_open,
            self.on_message,
            self.on_error,
            self.on_close,
            self.read_websocket
        )
