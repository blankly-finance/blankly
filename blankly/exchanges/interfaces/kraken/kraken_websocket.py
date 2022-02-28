import collections
import json
import ssl
import threading
import time
import traceback

import websocket
from websocket import create_connection

import blankly
import blankly.exchanges.interfaces.kraken.kraken_websocket_utils as websocket_utils
from blankly.exchanges.abc_exchange_websocket import ABCExchangeWebsocket
from blankly.utils.utils import info_print


class Tickers(ABCExchangeWebsocket):
    def __init__(self, symbol, stream, log=None,
                 pre_event_callback=None, initially_stopped=False, WEBSOCKET_URL="wss://ws.kraken.com"):
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

        self.__preferences = blankly.utils.load_user_preferences()

        self.URL = WEBSOCKET_URL
        self.ws = None
        self.__response = None
        self.__most_recent_tick = None
        self.__most_recent_time = None
        self.__thread = threading.Thread(target=self.read_websocket)
        self.__callbacks = []
        self.__pre_event_callback = pre_event_callback
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

        message = json.loads(message)
        print(message)
        if isinstance(message, dict):
            if message['status'] == 'subscribed':
                channel = message['channelName']
                info_print(f"Subscribed to {channel}")
                return
            elif message['status'] == 'heartbeat' or message['status'] == 'online':
                return
        else:
            if message[-2] == 'trade':
                self.__most_recent_time = message[1][0][2]
                self.__time_feed.append(self.__most_recent_time)
                #self.__log_response(self.__logging_callback, message)

                if self.__log:
                    if self.__message_count % 100 == 0:
                        self.__file.close()
                        self.__file = open(self.__filePath, 'a')
                    line = self.__logging_callback(message)
                    self.__file.write(line)

                # Manage price events and fire for each manager attached
                interface_message = self.__interface_callback(message)
                self.__ticker_feed.append(interface_message)
                self.__most_recent_tick = interface_message

                try:
                    for i in self.__callbacks:
                        i(interface_message)
                except Exception as e:
                    info_print(e)
                    traceback.print_exc()

                self.__message_count += 1

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        # This repeats the close behavior just in case something happens
        pass

    def on_open(self, ws):
        #ws = create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})
        request = json.dumps({
            "event": "subscribe",
            "pair": [
                self.__id
            ],
            "subscription": {
                "name": self.__stream
            }
        })
        ws.send(request)
        return ws

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
        if self.ws.connected:
            self.ws.close()
        else:
            print("Websocket for " + self.__id + '@' + self.__stream + " is already closed")

    """ Required in manager """

    def restart_ticker(self):
        self.start_websocket()
