import json
import time
import traceback

import requests

import blankly.exchanges.interfaces.okx.okx_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
from blankly.utils.utils import info_print

class Tickers(Websocket):
    def __init__(self, symbol, stream, log=None,
                 pre_event_callback=None, initially_stopped=False, WEBSOCKET_URL="wss://ws.okx.com:8443/ws/v5/public"):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "BTC-USD"
            log: Fill this with a path to a log file that should be created
            websocket_url: Default websocket URL feed.
        """
        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)

        super().__init__(symbol, stream, log, log_message, WEBSOCKET_URL, pre_event_callback)

        # Start the websocket
        if not initially_stopped:
            self.start_websocket(
                self.on_open,
                self.on_message,
                self.on_error,
                self.on_close,
                self.read_websocket
            )

    def read_websocket(self):
        # Main thread to sit here and run
        self.ws.run_forever()

    def on_message(self, ws, message):
        received_dict = json.loads(message)
        if received_dict['type'] == 'subscribed':
            info_print(f"Subscribed to {received_dict['channel']}")
            return
        parsed_received_trades = websocket_utils.process_trades(received_dict)
        for received in parsed_received_trades:
            # ISO8601 is converted to epoch in process_trades
            self.most_recent_time = received["time"]
            self.time_feed.append(self.most_recent_time)

            self.log_response(self.__logging_callback, received)

            # Manage price events and fire for each manager attached
            interface_message = self.__interface_callback(received)
            self.ticker_feed.append(interface_message)
            self.most_recent_tick = interface_message

            try:
                for i in self.callbacks:
                    i(interface_message)
            except Exception as e:
                info_print(e)
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
        self.start_websocket(
            self.on_open,
            self.on_message,
            self.on_error,
            self.on_close,
            self.read_websocket
        )