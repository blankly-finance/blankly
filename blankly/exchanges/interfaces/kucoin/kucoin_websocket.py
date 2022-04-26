"""
    Implementation for Kucoin Websockets
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
import time
import traceback

import blankly.exchanges.interfaces.kucoin.kucoin_websocket_utils as websocket_utils
from blankly.exchanges.interfaces.websocket import Websocket
from blankly.utils.utils import info_print


class Tickers(Websocket):
    def __init__(self, symbol, stream, websocket_url, log=None,
                 pre_event_callback=None, initially_stopped=False,
                 id_=None, **kwargs):
        """
        Create and initialize the ticker
        Args:
            symbol: Currency to initialize on such as "BTC-USD"
            log: Fill this with a path to a log file that should be created
            websocket_url: Default websocket URL feed.
        """
        self.id = id_
        self.__logging_callback, self.__interface_callback, log_message = websocket_utils.switch_type(stream)

        super().__init__(symbol, stream, log, log_message, websocket_url, pre_event_callback, kwargs)

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
        """
        Exchange specific actions to perform when receiving a message
        """
        # print(message)
        message = json.loads(message)

        if message['type'] == 'subscribe':
            channel = message['topic'].split(":", 1)[0].split("/", 2)[2]
            info_print(f"Subscribed to {channel}")
            return
        elif message['type'] == 'welcome' or message['type'] == 'ack':
            return

        # parsed_received_trades = websocket_utils.trade_interface(message)

        # for received in parsed_received_trades:
            # ISO8601 is converted to epoch in process_trades
        self.most_recent_time = time.time()
        self.time_feed.append(self.most_recent_time)

        self.log_response(self.__logging_callback, message)

        # Manage price events and fire for each manager attached
        interface_message = self.__interface_callback(message)
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
            'id': self.id,
            'type': 'subscribe',
            'topic': f'/market/{self.stream}:{self.symbol}',
            'privateChannel': False,
            'response': True
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
