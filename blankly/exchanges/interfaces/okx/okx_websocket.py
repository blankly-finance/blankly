"""
    Implementation for Okx Websockets
    Copyright (C) 2022  Emerson Dove

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

import blankly.exchanges.interfaces.okx.okx_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
from blankly.utils.utils import info_print


class Tickers(Websocket):
    def __init__(self, symbol, stream, log=None,
                 pre_event_callback=None, initially_stopped=False, WEBSOCKET_URL="wss://ws.okx.com:8443/ws/v5/public",
                 **kwargs):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "BTC-USD"
            log: Fill this with a path to a log file that should be created
            websocket_url: Default websocket URL feed.
        """
        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)

        super().__init__(symbol, stream, log, log_message, WEBSOCKET_URL, pre_event_callback, kwargs)

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
        self.checked = False

    def read_websocket(self):
        # Main thread to sit here and run
        self.ws.run_forever()

    def on_message(self, ws, message):
        received_dict = json.loads(message)
        if len(received_dict) == 2 and self.checked is not True:
            info_print(f"Subscribed to {received_dict['arg']['channel']}")
            self.checked = True
            return
        if (self.pre_event_callback is not None) and (not self.__pre_event_callback_filled) and \
                (self.stream == "books"):
            if received_dict['action'] == 'snapshot':
                try:
                    self.pre_event_callback(received_dict)
                except Exception:
                    traceback.print_exc()

            self.__pre_event_callback_filled = True
            return

        self.most_recent_time = received_dict['data'][0]["ts"]
        received_dict['data'][0]["ts"] = self.most_recent_time
        self.time_feed.append(self.most_recent_time)
        self.log_response(self.__logging_callback, received_dict['data'][0])

        # Manage price events and fire for each manager attached
        if self.stream == "books":
            interface_message = self.__interface_callback(received_dict)
        else: # self.stream == 'tickers':
            interface_message = self.__interface_callback(received_dict['data'][0])
        self.ticker_feed.append(interface_message)
        self.most_recent_tick = interface_message

        try:
            for i in self.callbacks:
                i(interface_message, **self.kwargs)
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
            'op': 'subscribe',
            'args': [{
                'channel': self.stream,
                'instId': self.symbol,
                }]
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
