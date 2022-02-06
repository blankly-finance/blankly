"""
    FTX websocket definitions
    Copyright (C) 2021 Blankly Finance

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
import traceback
import blankly
import blankly.exchanges.interfaces.ftx.ftx_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
# from blankly.utils import time
from blankly.utils.utils import info_print


# def create_ticker_connection(id_, url, channel):
#     ws = create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE})
#     request = json.dumps({
#         "op": "subscribe",
#         "channel": channel,
#         "market": id_
#     })
#     ws.send(request)
#     return ws


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
                 pre_event_callback=None, initially_stopped=False, WEBSOCKET_URL="wss://ftx.com/ws/"):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "BTC-USD"
            log: Fill this with a path to a log file that should be created
            WEBSOCKET_URL: Default websocket URL feed.
        """
        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)

        super().__init__(symbol, stream, log, log_message, WEBSOCKET_URL, pre_event_callback)

        self.__pre_event_callback_filled = False


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
        """
        This is the target that runs
        """
        self.ws.run_forever()

    def on_message(self, ws, message):
        """
        Behavior for this exchange
        """
        #received_string = message
        received = json.loads(message)
        if received['type'] == 'subscribed':
            info_print(f"Subscribed to {received['channel']}")
            return

        # self.pre_event_callback(received_dict)

        if (self.pre_event_callback is not None) and (not self.__pre_event_callback_filled) and \
                (self.stream == "orderbook"):
            if received['type'] == 'partial':
                try:
                    self.pre_event_callback(received)
                except Exception:
                    traceback.print_exc()

            self.__pre_event_callback_filled = True
            return

        # parsed_received_trades = websocket_utils.process_trades(received_dict)
        # for received in parsed_received_trades:
            # ISO8601 is converted to epoch in process_trades
        self.most_recent_time = blankly.utils.convert_epochs(received['data']['time'])
        received["data"]["time"] = self.most_recent_time
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
            "op": "subscribe",
            "channel": self.stream,
            "market": self.symbol
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

# if __name__ == "__main__":
#     a = Tickers('a', 'b')
#
#     while True:
#         time.sleep(1)
