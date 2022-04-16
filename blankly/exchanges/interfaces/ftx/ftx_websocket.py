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
from blankly.utils.utils import epoch_from_iso8601, to_blankly_symbol
import blankly.exchanges.interfaces.ftx.ftx_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
from blankly.utils.utils import info_print


class Tickers(Websocket):
    def __init__(self, symbol, stream, log=None,
                 pre_event_callback=None, initially_stopped=False, websocket_url="wss://ftx.com/ws/", **kwargs):
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
        received_dict = json.loads(message)
        if received_dict['type'] == 'subscribed':
            info_print(f"Subscribed to {received_dict['channel']}")
            return

        if (self.pre_event_callback is not None) and (not self.__pre_event_callback_filled) and \
                (self.stream == "orderbook"):
            if received_dict['type'] == 'partial':
                try:
                    self.pre_event_callback(received_dict)
                except Exception:
                    traceback.print_exc()

            self.__pre_event_callback_filled = True
            return

        if self.stream == "orderbook":
            interface_response = self.__interface_callback(received_dict['data'])
            self.most_recent_time = interface_response["time"]
            self.time_feed.append(self.most_recent_time)
            self.most_recent_tick = interface_response

            try:
                interface_response['symbol'] = received_dict['market']
                for i in self.callbacks:
                    i(interface_response, **self.kwargs)
            except Exception as e:
                info_print(e)
                traceback.print_exc()
        elif self.stream == "trades":
            for received in received_dict['data']:
                interface_response = self.__interface_callback(received)
                # This could be passed into the received var above which could be cleaner
                interface_response['symbol'] = to_blankly_symbol(received_dict['market'], 'ftx')
                self.ticker_feed.append(interface_response)

                self.most_recent_time = epoch_from_iso8601(received["time"])
                self.time_feed.append(self.most_recent_time)
                self.most_recent_tick = received

                self.log_response(self.__logging_callback, received)

                try:
                    for i in self.callbacks:
                        i(interface_response)
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
