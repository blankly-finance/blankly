import collections
import json
import ssl
import threading
import time
import traceback

from websocket import create_connection

import blankly
import blankly.exchanges.interfaces.ftx.ftx_websocket_utils as websocket_utils
from blankly.exchanges.abc_exchange_websocket import ABCExchangeWebsocket


def create_ticker_connection(id_, url, channel):
    ws = create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})
    request = json.dumps({
        "op": "subscribe",
        "channel": channel,
        "market": id_
    })
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


class Tickers(ABCExchangeWebsocket):
    def __init__(self, symbol, stream, log=None,
                 pre_event_callback=None, initially_stopped=False, WEBSOCKET_URL="wss://ftx.com/ws/"):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "BTC-USD"
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

        self.URL = WEBSOCKET_URL
        self.ws = None
        self.__response = None
        self.__most_recent_tick = None
        self.__most_recent_time = None
        self.__callbacks = []
        self.__pre_event_callback = pre_event_callback

        # Reload preferences
        self.__preferences = blankly.utils.load_user_preferences()
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
            self.ws = create_ticker_connection(self.__id, self.URL, self.__stream)
            self.__response = self.ws.recv()
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
        counter = 0
        # TODO port this to "WebSocketApp" found in the websockets documentation
        while self.ws.connected:
            # In case the user closes while its reading from the websocket, this will let it expire
            persist_connected = self.ws.connected
            try:
                received_string = self.ws.recv()
                received_dict = json.loads(received_string)
                parsed_received_trades = websocket_utils.process_trades(received_dict)
                for received in parsed_received_trades:
                    # ISO8601 is converted to epoch in process_trades
                    self.__most_recent_time = received["time"]
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
                    self.ws = create_ticker_connection(self.__id, self.URL, self.__stream)
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

    def get_feed(self):
        return list(self.__ticker_feed)

    """ Required in manager """

    def get_response(self):
        return self.__response

    """ Required in manager """

    def close_websocket(self):
        if self.ws.connected:
            self.ws.close()
        else:
            print("Websocket for " + self.__id + ' on channel ' + self.__stream + " is already closed")

    """ Required in manager """

    def restart_ticker(self):
        self.start_websocket()
