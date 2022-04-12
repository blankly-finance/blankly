"""
    binance ticker class.
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
import traceback

import blankly
import blankly.exchanges.interfaces.binance.binance_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
from blankly.utils.utils import info_print


class Tickers(Websocket):
    def __init__(self, symbol, stream, log=None, initially_stopped=False,
                 websocket_url="wss://stream.binance.{}:9443/ws", **kwargs):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "btcusdt"
            stream: Stream to use, such as "depth" or "trade"
            log: Fill this with a path to a log file that should be created
            websocket_url: Default websocket URL feed.
        """
        # Reload preferences
        self.__preferences = blankly.utils.load_user_preferences()

        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)
        url = websocket_url.format(self.__preferences['settings']['binance']['binance_tld'])

        super().__init__(symbol, stream, log, log_message, url, None, kwargs)

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
        # This repeats the close behavior just in case something happens

    def on_message(self, ws, message):
        """
        Exchange specific actions to perform when receiving a message
        """
        self.message_count += 1
        message = json.loads(message)
        try:
            self.most_recent_time = message['E']
            self.time_feed.append(self.most_recent_time)

            self.log_response(self.__logging_callback, message)

            interface_message = self.__interface_callback(message)
            self.ticker_feed.append(interface_message)
            self.most_recent_tick = interface_message
            for i in self.callbacks:
                i(interface_message, **self.kwargs)
        except KeyError:
            # If the try below figures this out then we don't have to traceback
            error_found = False
            try:
                if message['result'] is None:
                    self.response = message
                    error_found = True
            except KeyError:
                traceback.print_exc()

            if not error_found:
                traceback.print_exc()

    def on_error(self, ws, error):
        info_print(error)

    def on_close(self, ws):
        # This repeats the close behavior just in case something happens
        pass

    def on_open(self, ws):
        request = json.dumps({
            'method': 'SUBSCRIBE',
            'params': [f'{self.symbol}@{self.stream}'],
            'id': 1
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
